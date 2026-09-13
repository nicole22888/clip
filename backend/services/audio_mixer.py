import ffmpeg

class AudioMixService:
    @staticmethod
    def process_and_mix_tracks(game_audio_node, voiceover_path: str, pad_duration: float, total_length: float):
        """
        ENTERPRISE DUCKING MIXER: Implements sidechain envelope compression, 
        clears low frequency rumbles, and fixes multi-edge node splitting loops using explicit split tracking.
        """
        # Load the clean independent narration .mp3 file
        voice_input = ffmpeg.input(voiceover_path).audio
        
        # 1. NORMALIZE VOICE TIMINGS: Defensive padding and exact trimming loops
        normalized_voice = (
            voice_input
            .filter('aformat', sample_rates=48000, channel_layouts='stereo')
            .filter('apad', pad_dur=total_length)
            .filter('atrim', duration=total_length)
        )
        
        # Fix the Multi-Outgoing Edge error using explicit asset splitting!
        # This duplicates the voice track into two independent lanes in memory
        voice_lane_A, voice_lane_B = normalized_voice.asplit()

        # 2. AUDIO RESOLUTION & EQUALIZATION CHANNEL
        # Uses parametric equalizers to drop hums below 150Hz while expanding high-frequency audio signatures
        game_clean = (
            game_audio_node
            .filter('firequalizer', gain_mono='if(lt(f,150),-24,0)')
            .filter('aformat', sample_rates=48000, channel_layouts='stereo')
            .filter('apad', pad_dur=pad_duration)
            .filter('atrim', duration=total_length)
        )

        # 3. HIGH-FIDELITY SIDECHAIN ENVELOPE DUCKING
        # Dynamically reduces game sounds by exactly your ratio targets ONLY during live narration voice bursts
        ducked_gameplay = ffmpeg.filter(
            [game_clean, voice_lane_A],
            'sidechaincompress',
            threshold='-22dB',
            ratio='4.5',
            attack='12',
            release='180'
        )

        # 4. FINAL PRODUCTION MASTER MIXING & AUDIO LIMITER LAYER
        final_mixed_audio = (
            ffmpeg
            .filter([ducked_gameplay, voice_lane_B], 'amix', inputs=2, duration='first')
            .filter('alimiter', limit=0.95, level=True) # Protects speakers against volume clipping distortion
        )
        
        return final_mixed_audio
