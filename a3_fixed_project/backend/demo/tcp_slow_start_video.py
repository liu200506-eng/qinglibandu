import io
import json
import os
import subprocess
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


class TCPSlowStartAnimator:
    def __init__(self, ssthresh: int = 8, initial_cwnd: int = 1, max_rtt: int = 15):
        self.ssthresh = ssthresh
        self.initial_cwnd = initial_cwnd
        self.max_rtt = max_rtt
        self.cwnd_history: List[int] = []
        self.rtt_history: List[int] = []
        self.phase_history: List[str] = []
        self._generate_data()

    def _generate_data(self):
        cwnd = self.initial_cwnd
        for rtt in range(1, self.max_rtt + 1):
            self.cwnd_history.append(cwnd)
            self.rtt_history.append(rtt)
            
            if cwnd < self.ssthresh:
                self.phase_history.append("Slow Start")
                cwnd *= 2
            else:
                self.phase_history.append("Congestion Avoidance")
                cwnd += 1

    def create_frames(self, output_dir: str) -> List[str]:
        frame_files = []
        os.makedirs(output_dir, exist_ok=True)

        for frame_idx, frame in enumerate(range(len(self.rtt_history))):
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=100)
            fig.suptitle('TCP Slow Start & Congestion Avoidance', fontsize=16, fontweight='bold')

            ax1.set_xlabel('RTT Round')
            ax1.set_ylabel('cwnd (segments)')
            ax1.set_ylim(0, max(self.cwnd_history) + 5)
            ax1.set_xlim(0, self.max_rtt + 2)
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            ax2.set_xlabel('RTT Round')
            ax2.set_ylabel('Phase')
            ax2.set_xlim(0, self.max_rtt + 2)
            ax2.set_ylim(-0.5, 1.5)
            ax2.set_yticks([0, 1])
            ax2.set_yticklabels(['Slow Start', 'Congestion Avoidance'])
            ax2.grid(True, linestyle='--', alpha=0.7)

            x = self.rtt_history[:frame+1]
            y = self.cwnd_history[:frame+1]
            
            ax1.plot(x, y, 'b-o', linewidth=3, markersize=10, label='cwnd')
            ax1.axhline(y=self.ssthresh, color='r', linestyle='--', linewidth=2, 
                       label=f'ssthresh={self.ssthresh}')
            
            phase_colors = ['#4CAF50' if p == 'Slow Start' else '#FF9800' for p in self.phase_history[:frame+1]]
            ax2.bar(x, [1] * len(x), width=0.8, color=phase_colors, alpha=0.7)

            ax1.legend()

            ax1.text(0.02, 0.95, f'RTT Round: {x[-1]}', transform=ax1.transAxes, 
                    fontsize=12, fontweight='bold')
            ax1.text(0.02, 0.90, f'cwnd = {y[-1]}', transform=ax1.transAxes, 
                    fontsize=12)
            ax1.text(0.02, 0.85, f'Phase: {self.phase_history[frame]}', transform=ax1.transAxes, 
                    fontsize=12)

            frame_path = os.path.join(output_dir, f"frame_{frame_idx:03d}.png")
            plt.savefig(frame_path, dpi=100, bbox_inches='tight')
            frame_files.append(frame_path)
            plt.close(fig)

        return frame_files


def generate_script(student_level: str = "beginner") -> Dict[str, str]:
    scripts = {
        "beginner": {
            "voiceover": "Hello everyone. Today we will learn about TCP slow start mechanism. TCP is a reliable transport protocol. It needs to establish a connection before sending data. However, if we send a large amount of data at once, it may cause network congestion. So TCP uses a slow start strategy. The core idea is to send only a small amount of data at first, then gradually increase the sending rate based on network feedback. We use cwnd, the congestion window, to control the sending speed. Initially cwnd equals 1, meaning only 1 segment can be sent. After each RTT, if we receive an acknowledgment, cwnd doubles. You can see cwnd grows from 1 to 2, then to 4, then to 8. This is exponential growth. When cwnd reaches ssthresh, the slow start threshold, we enter the congestion avoidance phase. In this phase, cwnd increases by 1 per RTT instead of doubling. This allows us to probe network capacity more cautiously and avoid congestion. To summarize: slow start phase has exponential cwnd growth, congestion avoidance phase has linear growth. This is the basic principle of TCP slow start.",
            "subtitles": [
                {"time": "0,5", "text": "Hello everyone. Today we will learn about TCP slow start."},
                {"time": "5,10", "text": "TCP needs to establish connection before sending data."},
                {"time": "10,15", "text": "Sending too much data at once may cause congestion."},
                {"time": "15,20", "text": "TCP uses slow start: send small amount first."},
                {"time": "20,25", "text": "cwnd controls sending speed. Initially cwnd=1."},
                {"time": "25,30", "text": "After each RTT, if ACK received, cwnd doubles."},
                {"time": "30,35", "text": "cwnd grows exponentially: 1, 2, 4, 8..."},
                {"time": "35,40", "text": "When cwnd reaches ssthresh, enter congestion avoidance."},
                {"time": "40,45", "text": "In congestion avoidance, cwnd increases linearly."},
                {"time": "45,50", "text": "This probes network capacity more cautiously."},
                {"time": "50,55", "text": "Summary: exponential growth then linear growth."},
                {"time": "55,60", "text": "This is the basic principle of TCP slow start."}
            ]
        },
        "intermediate": {
            "voiceover": "Hello students. Today we analyze TCP slow start in depth. Slow start is the first phase of TCP congestion control. The sender maintains a congestion window cwnd, whose value determines the maximum number of segments the sender can transmit before receiving acknowledgments. Initially, cwnd is set to 1 MSS. For each ACK received, cwnd increases by 1. After each RTT, cwnd approximately doubles. This exponential growth allows rapid probing of available bandwidth but may also cause network congestion. Therefore, a slow start threshold ssthresh is introduced. When cwnd is less than ssthresh, slow start is used. When cwnd is greater or equal to ssthresh, the algorithm switches to congestion avoidance. In congestion avoidance phase, cwnd grows linearly, increasing by 1 MSS per RTT. This strategy is more conservative and prevents network congestion. Note that when packet loss occurs, ssthresh is set to half of current cwnd, and cwnd resets to 1, re-entering slow start phase. This is TCP's fast recovery mechanism.",
            "subtitles": [
                {"time": "0,5", "text": "Hello students. Today we analyze TCP slow start in depth."},
                {"time": "5,10", "text": "Sender maintains congestion window cwnd."},
                {"time": "10,15", "text": "Initially cwnd is set to 1 MSS."},
                {"time": "15,20", "text": "After each RTT, cwnd approximately doubles."},
                {"time": "20,25", "text": "Exponential growth probes available bandwidth quickly."},
                {"time": "25,30", "text": "Slow start threshold ssthresh controls growth."},
                {"time": "30,35", "text": "When cwnd >= ssthresh, switch to congestion avoidance."},
                {"time": "35,40", "text": "Congestion avoidance: cwnd grows linearly."},
                {"time": "40,45", "text": "This prevents network congestion."},
                {"time": "45,50", "text": "On packet loss, ssthresh = cwnd/2."},
                {"time": "50,55", "text": "cwnd resets to 1, re-enter slow start."}
            ]
        },
        "advanced": {
            "voiceover": "Today we analyze TCP slow start from a mathematical perspective. The core equation is: cwnd = min(cwnd + 1, ssthresh) when ACK is received. Since multiple ACKs can be received per RTT, cwnd approximately doubles per RTT. Let initial cwnd = W0. After n RTTs, cwnd(n) = W0 * 2^n. When cwnd(n) >= ssthresh, switch to congestion avoidance: cwnd(n) = ssthresh + n. From throughput perspective, TCP throughput T = (cwnd * MSS) / RTT. In slow start, throughput grows exponentially: T(n) = (W0 * 2^n * MSS) / RTT. However, this rapid growth may cause queue overflow and packet loss. Therefore, ssthresh selection is crucial. Modern TCP variants like CUBIC introduce more complex growth functions, ensuring fast convergence while avoiding congestion. Understanding the mathematical essence of slow start helps design more efficient transport protocols.",
            "subtitles": [
                {"time": "0,5", "text": "Today we analyze TCP slow start mathematically."},
                {"time": "5,10", "text": "Core equation: cwnd = min(cwnd + 1, ssthresh)."},
                {"time": "10,15", "text": "After n RTTs: cwnd(n) = W0 * 2^n."},
                {"time": "15,20", "text": "When cwnd >= ssthresh, switch to congestion avoidance."},
                {"time": "20,25", "text": "TCP throughput T = (cwnd * MSS) / RTT."},
                {"time": "25,30", "text": "Slow start: throughput grows exponentially."},
                {"time": "30,35", "text": "Rapid growth may cause queue overflow."},
                {"time": "35,40", "text": "ssthresh selection is crucial."},
                {"time": "40,45", "text": "Modern TCP: CUBIC and complex growth functions."},
                {"time": "45,50", "text": "Fast convergence while avoiding congestion."},
                {"time": "50,55", "text": "Understanding math helps design better protocols."}
            ]
        }
    }

    return scripts.get(student_level, scripts["beginner"])


def create_html_player(output_dir: str, frame_files: List[str], script: Dict[str, str], student_level: str) -> str:
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TCP Slow Start Animation - {student_level}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #4CAF50, #00BCD4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header p {{
            font-size: 1.2em;
            color: #b0b0b0;
        }}
        .video-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }}
        #animation-frame {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }}
        .controls {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .control-btn {{
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .control-btn:hover {{
            transform: translateY(-2px);
        }}
        #play-btn {{
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
        }}
        #pause-btn {{
            background: linear-gradient(90deg, #ff9800, #f57c00);
            color: white;
        }}
        #reset-btn {{
            background: linear-gradient(90deg, #f44336, #da190b);
            color: white;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            margin-top: 20px;
            cursor: pointer;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #00BCD4);
            border-radius: 4px;
            width: 0%;
            transition: width 0.1s ease;
        }}
        .timeline {{
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 12px;
            color: #888;
        }}
        .subtitles {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .subtitles h3 {{
            color: #4CAF50;
            margin-bottom: 15px;
        }}
        .subtitle-item {{
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 14px;
            line-height: 1.5;
        }}
        .subtitle-item.active {{
            background: rgba(76, 175, 80, 0.2);
            border-left: 4px solid #4CAF50;
        }}
        .info-panel {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 20px;
        }}
        .info-panel h3 {{
            color: #00BCD4;
            margin-bottom: 15px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .info-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 8px;
        }}
        .info-card .label {{
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }}
        .info-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TCP Slow Start & Congestion Avoidance</h1>
        <p>Interactive Demo - {student_level.capitalize()} Level</p>
    </div>

    <div class="video-container">
        <img id="animation-frame" src="{frame_files[0]}" alt="Animation Frame">
        <div class="controls">
            <button class="control-btn" id="play-btn">▶ Play</button>
            <button class="control-btn" id="pause-btn">⏸ Pause</button>
            <button class="control-btn" id="reset-btn">↺ Reset</button>
        </div>
        <div class="progress-bar" id="progress-bar">
            <div class="progress-fill" id="progress-fill"></div>
        </div>
        <div class="timeline">
            <span id="current-time">0:00</span>
            <span id="total-time">{len(frame_files) * 1.2:.1f}s</span>
        </div>
    </div>

    <div class="subtitles">
        <h3>📝 Subtitles</h3>
        {''.join([f'<div class="subtitle-item" id="subtitle-{i}">{sub["text"]}</div>' for i, sub in enumerate(script['subtitles'])])}
    </div>

    <div class="info-panel">
        <h3>📊 Key Concepts</h3>
        <div class="info-grid">
            <div class="info-card">
                <div class="label">Initial cwnd</div>
                <div class="value">1 segment</div>
            </div>
            <div class="info-card">
                <div class="label">ssthresh</div>
                <div class="value">8 segments</div>
            </div>
            <div class="info-card">
                <div class="label">Slow Start Growth</div>
                <div class="value">Exponential</div>
            </div>
            <div class="info-card">
                <div class="label">Congestion Avoidance</div>
                <div class="value">Linear</div>
            </div>
        </div>
    </div>

    <script>
        const frames = {json.dumps(frame_files)};
        const subtitles = {json.dumps(script['subtitles'])};
        let currentFrame = 0;
        let isPlaying = false;
        let intervalId = null;
        const frameDelay = 1200;

        const frameImg = document.getElementById('animation-frame');
        const progressFill = document.getElementById('progress-fill');
        const currentTimeEl = document.getElementById('current-time');
        const totalTimeEl = document.getElementById('total-time');

        function updateFrame() {{
            frameImg.src = frames[currentFrame];
            const progress = (currentFrame / (frames.length - 1)) * 100;
            progressFill.style.width = progress + '%';
            const time = (currentFrame * frameDelay) / 1000;
            currentTimeEl.textContent = time.toFixed(1) + 's';
            
            document.querySelectorAll('.subtitle-item').forEach((el, i) => {{
                el.classList.remove('active');
                if (i < subtitles.length && time >= parseInt(subtitles[i].time.split(',')[0]) && time <= parseInt(subtitles[i].time.split(',')[1])) {{
                    el.classList.add('active');
                }}
            }});
        }}

        function play() {{
            if (isPlaying) return;
            isPlaying = true;
            intervalId = setInterval(() => {{
                currentFrame++;
                if (currentFrame >= frames.length) {{
                    currentFrame = frames.length - 1;
                    pause();
                }}
                updateFrame();
            }}, frameDelay);
        }}

        function pause() {{
            isPlaying = false;
            if (intervalId) {{
                clearInterval(intervalId);
                intervalId = null;
            }}
        }}

        function reset() {{
            pause();
            currentFrame = 0;
            updateFrame();
        }}

        document.getElementById('play-btn').addEventListener('click', play);
        document.getElementById('pause-btn').addEventListener('click', pause);
        document.getElementById('reset-btn').addEventListener('click', reset);

        document.getElementById('progress-bar').addEventListener('click', (e) => {{
            const rect = e.target.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            currentFrame = Math.floor(percent * (frames.length - 1));
            updateFrame();
        }});

        updateFrame();
    </script>
</body>
</html>"""

    html_path = os.path.join(output_dir, f"tcp_slow_start_{student_level}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return html_path


def generate_tcp_video(output_dir: str = None, student_level: str = "beginner") -> Dict[str, str]:
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    frames_dir = os.path.join(output_dir, f"frames_{student_level}")
    
    script = generate_script(student_level)
    
    animator = TCPSlowStartAnimator(ssthresh=8, initial_cwnd=1, max_rtt=12)
    print("[INFO] Creating TCP slow start animation frames...")
    frame_files = animator.create_frames(frames_dir)
    print(f"[INFO] Generated {len(frame_files)} frames")

    print("[INFO] Creating HTML player...")
    html_path = create_html_player(output_dir, [f"frames_{student_level}/" + os.path.basename(f) for f in frame_files], script, student_level)
    print(f"[INFO] HTML player saved to {html_path}")

    return {
        "html_path": html_path,
        "frames_dir": frames_dir,
        "frame_count": len(frame_files),
        "student_level": student_level,
        "script": script
    }


if __name__ == "__main__":
    print("=" * 60)
    print("TCP Slow Start Video Generator")
    print("=" * 60)

    for level in ["beginner", "intermediate", "advanced"]:
        print(f"\n[PROCESSING] Generating video for {level} level...")
        result = generate_tcp_video(student_level=level)
        print(f"[COMPLETE] HTML Player: {result['html_path']}")

    print("\n" + "=" * 60)
    print("All animations generated! Open HTML files in browser to view.")
    print("=" * 60)
