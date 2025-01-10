import gradio as gr
import requests

def generate_voice_frontend(text, language, ref_audio, transcribed_text):
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/generate',  # 將請求發送到 Flask API
            data={'text': text, 'language': language, 'transcribed_text': transcribed_text},
            files={'ref_audio': open(ref_audio, 'rb')}
        )
        if response.status_code == 200:
            result = response.json()
            return result["audio_url"]
        else:
            return "生成失败，请重试"
    except Exception as e:
        return f"发生错误: {str(e)}"

# Gradio 界面設置
with gr.Blocks(css=".gradio-container {background-color: #f0f0f0;}") as demo:
    gr.Markdown("# GPT-SoVITS 语音生成器")
    
    with gr.Row():
        text_input = gr.Textbox(lines=5, placeholder="请输入希望模仿生成的文本...", label="输入文本")
        transcribed_text_input = gr.Textbox(lines=5, placeholder="请输入上傳音频的内容...", label="输入转录文本")
        language_input = gr.Dropdown(choices=["zh", "en", "jp"], label="语言选择")
    
    ref_audio_input = gr.Audio(type="filepath", label="上传参考音频 (3~10 秒)")
    output_audio = gr.Audio(label="生成的音频")
    
    generate_button = gr.Button("生成语音")
    generate_button.click(generate_voice_frontend, inputs=[text_input, language_input, ref_audio_input, transcribed_text_input], outputs=output_audio)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=9872, debug=True)
