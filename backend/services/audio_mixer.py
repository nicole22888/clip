import ffmpeg

class AudioMixService:
    @staticmethod
    def process_and_mix_tracks(game_audio_node, voiceover_path: str, pad_duration: float, total_length: float, audio_fx_tag: str = "clean_studio"):
        """
        ENTERPRISE DUCKING MIXER: Automatically parses AI environment tags to apply walkie-talkies, 
        hall reverbs, or megaphone effects dynamically to the voice track without hardcoding.
        """
        voice_input = ffmpeg.input(voiceover_path).audio
        
        # 1. NORMALIZE VOICE TIMINGS
        normalized_base_voice = (
            voice_input
            .filter('aformat', sample_rates=48000, channel_layouts='stereo')
            .filter('apad', pad_dur=total_length)
            .filter('atrim', duration=total_length)
        )
        
        # 2. DYNAMIC SONIC FILTER SWITCHER
        # Reads the string value returned by the AI and routes it down specific FFmpeg signal chains
        fx = str(audio_fx_tag).strip().lower()
        if fx == "walkie_talkie":
            # Aggressive bandpass radio curves + overdrive clipping crunch
            processed_voice = (
                normalized_base_voice
                .filter('highpass', frequency=400)
                .filter('lowpass', frequency=3400)
                .filter('overdrive', gain=8)
            )
        elif fx == "megaphone":
            # High-gain resonance filter
            processed_voice = (
                normalized_base_voice
                .filter('highpass', frequency=600)
                .filter('lowpass', frequency=2500)
                .filter('volume', volume=1.4)
            )
        elif fx == "hall_reverb":
            # Spacious echo acoustics delay map
            processed_voice = normalized_base_voice.filter('aecho', 0.8, 0.8, 40, 0.4)
        else:
            # clean_studio fallback: Keep voice completely un-distorted
            processed_voice = normalized_base_voice

        # Duplicate the processed stream to prevent multi-outgoing-edge lookup faults
        voice_split_node = processed_voice.filter('asplit', 2)
        voice_lane_A = voice_split_node
        voice_lane_B = voice_split_node

        # 3. GAMEPLAY AUDIO CLEANUP
        game_clean = (
            game_audio_node
            .filter('firequalizer', mono='if(lt(f,150),-24,0)')
            .filter('aformat', sample_rates=48000, channel_layouts='stereo')
            .filter('apad', pad_dur=pad_duration)
            .filter('atrim', duration=total_length)
        )

        # 4. SIDECHAIN COMPRESSION ENVELOPE DUCKING
        ducked_gameplay = ffmpeg.filter(
            [game_clean, voice_lane_A],
            'sidechaincompress',
            threshold='-22dB',
            ratio='4.5',
            attack='12',
            release='180'
        )

        # 5. MASTER MIXDOWN LAYER
        final_mixed_audio = (
            ffmpeg
            .filter([ducked_gameplay, voice_lane_B], 'amix', inputs=2, duration='first')
            .filter('alimiter', limit=0.95, level=True)
        )
        
        return final_mixed_audio
