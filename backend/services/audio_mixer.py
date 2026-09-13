import ffmpeg

class AudioMixService:
    @staticmethod
    def process_and_mix_tracks(game_audio_node, voiceover_path: str, pad_duration: float, total_length: float, audio_fx_tag: str = "clean_studio"):
        """
        ENTERPRISE DUCKING MIXER: Maps AI environment tags and satisfies FFmpeg parameter 
        mappings by utilizing the documented 'gain' argument inside firequalizer.
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
        fx = str(audio_fx_tag).strip().lower()
        if fx == "walkie_talkie":
            processed_voice = (
                normalized_base_voice
                .filter('highpass', frequency=400)
                .filter('lowpass', frequency=3400)
                .filter('overdrive', gain=8)
            )
        elif fx == "megaphone":
            processed_voice = (
                normalized_base_voice
                .filter('highpass', frequency=600)
                .filter('lowpass', frequency=2500)
                .filter('volume', volume=1.4)
            )
        elif fx == "hall_reverb":
            processed_voice = normalized_base_voice.filter('aecho', 0.8, 0.8, 40, 0.4)
        else:
            processed_voice = normalized_base_voice

        # DOCUMENTED MULTI-EDGE FIX: Explicitly extract the indexed output tracks!
        # Splitting a filter generates an array list of nodes. Referencing index 0 and 1 
        # gives FFmpeg separate, unique lane handles in memory, ending the graph crash.
        voice_split_node = processed_voice.filter('asplit', 2)
        voice_lane_A = voice_split_node[0]
        voice_lane_B = voice_split_node[1]

        # 3. GAMEPLAY AUDIO CLEANUP
        game_clean = (
            game_audio_node
            .filter('firequalizer', gain='if(lt(f,150),-24,0)')
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
