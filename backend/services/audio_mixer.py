import ffmpeg

class AudioMixService:
    @staticmethod
    def process_and_mix_tracks(game_audio_node, voiceover_path: str, pad_duration: float, total_length: float):
        """
        ENTERPRISE DUCKING MIXER: Implements sidechain envelope compression, 
        clears low frequency rumbles, and fixes multi-edge node splitting loops using verified asplit syntax.
        """
        voice_input = ffmpeg.input(voiceover_path).audio
        
        # 1. NORMALIZE VOICE TIMINGS: Defensive padding and exact trimming loops
        normalized_voice = (
            voice_input
            .filter('aformat', sample_rates=48000, channel_layouts='stereo')
            .filter('apad', pad_dur=total_length)
            .filter('atrim', duration=total_length)
        )
        
        # CORRECTED VERIFIED SYNTAX: Call the native 'asplit' filter with explicit output lanes count.
        # This duplicates the voice node track into two completely separate wires in memory safely!
        voice_split_node = normalized_voice.filter_multi_output('asplit', 2)
        voice_lane_A = voice_split_node[0]
        voice_lane_B = voice_split_node[1]

        # 2. AUDIO RESOLUTION & EQUALIZATION CHANNEL
        game_clean = (
            game_audio_node
            .filter('firequalizer', gain_mono='if(lt(f,150),-24,0)')
            .filter('aformat', sample_rates=48000, channel_layouts='stereo')
            .filter('apad', pad_dur=pad_duration)
            .filter('atrim', duration=total_length)
        )

        # 3. HIGH-FIDELITY SIDECHAIN ENVELOPE DUCKING
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
            .filter('alimiter', limit=0.95, level=True)
        )
        
        return final_mixed_audio
