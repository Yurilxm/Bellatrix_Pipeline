import sys
import os
if sys.stdout.encoding != 'utf-8': sys.stdout.reconfigure(encoding='utf-8')
import argparse
import shutil
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda
from core.validator import is_video_valid
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar
from core.governance import gerar_nome_final
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich_argparse import RichHelpFormatter

console = Console()

def processar_video(input_path, output_format="mxf", duracao_alvo=180, gerar_legenda=True, texto_materia="", prompt_customizado=""):
    console.print(f"\n[bold cyan]🚀 Iniciando Pipeline para:[/bold cyan] [white]{input_path}[/white]")
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        console.print(f"[bold red]❌ Vídeo inválido: {mensagem}[/bold red]")
        return
    console.print(f"[green]✅ {mensagem}[/green]")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = "temp_cortes"
    os.makedirs(temp_dir, exist_ok=True)
    
    console.print("[yellow]⏳ [1/4] Detectando blocos (fades)...[/yellow]")
    detector = DetectorFadesPretos(input_path)
    blocos = detector.detectar()
    console.print(f"[green]✅ {len(blocos)} blocos encontrados.[/green]")
    
    console.print("[yellow]⏳ [2/4] Transcrevendo áudio (Whisper)...[/yellow]")
    srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
    transcrever_e_gerar_srt(input_path, srt_temp)
    console.print("[green]✅ Transcrição concluída.[/green]")
    
    console.print("[yellow]⏳ [3/4] Selecionando melhores trechos (LLM gerando 3 Opções)...[/yellow]")
    resposta_llm = analisar_e_selecionar(blocos, srt_temp, texto_materia, duracao_alvo, prompt_customizado)
    opcoes = resposta_llm.get("opcoes", [])
    console.print(f"[green]✅ {len(opcoes)} opções de edição geradas.[/green]")
    
    console.print(f"[yellow]⏳ [4/4] Renderizando os vídeos ({output_format.upper()})...[/yellow]")
    arquivos_finais = []
    
    for opcao in opcoes:
        opcao_id = opcao.get("id")
        nome_opcao = opcao.get("nome", f"Opcao{opcao_id}")
        cortes = opcao.get("cortes", [])
        
        cortes_gerados = []
        for i, trecho in enumerate(cortes):
            output_corte = os.path.join(temp_dir, f"op{opcao_id}_corte_{i}.{output_format}")
            cortar_video(input_path, output_corte, trecho["start"], trecho["end"], output_format)
            cortes_gerados.append(output_corte)
            
        video_final = gerar_nome_final(input_path, os.getcwd(), assunto=f"OPCAO{opcao_id}_{nome_opcao}")
        if len(cortes_gerados) > 1:
            juntar_videos(cortes_gerados, video_final, output_format)
        elif len(cortes_gerados) == 1:
            shutil.move(cortes_gerados[0], video_final)
            
        console.print(f"   -> [cyan]{nome_opcao}[/cyan] renderizada: {video_final}")
        arquivos_finais.append(video_final)

    shutil.rmtree(temp_dir)
    console.print(f"\n[bold green]🎉 Pipeline finalizada! {len(arquivos_finais)} arquivos gerados.[/bold green]\n")

def show_banner():
    banner = Text()
    banner.append("⚡ ", style="bold yellow")
    banner.append("BELLATRIX PIPELINE", style="bold cyan")
    banner.append(" (Edição Automatizada para TV)\n", style="bold white")
    banner.append("Gerando 3 opções de corte (Cartilha)", style="dim italic")
    console.print(Panel.fit(banner, border_style="cyan"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Microserviço de Edição Automatizada de Vídeo para TV.",
        epilog="Exemplo:\n  python main.py -i video.MXF -t 'Texto' -p 'Mais emoção'",
        formatter_class=RichHelpFormatter
    )
    group_input = parser.add_argument_group("📥 Entrada")
    group_input.add_argument("-i", "--input", required=True, help="Caminho do vídeo bruto.")
    group_input.add_argument("-t", "--texto", default="", help="Texto da matéria (roteiro).")
    group_input.add_argument("-p", "--prompt", default="", help="Prompt customizado para a IA (ex: 'mais emoção').")

    group_output = parser.add_argument_group("📤 Saída")
    group_output.add_argument("-o", "--output_format", default="mxf", choices=["mp4", "mxf", "mov", "mkv"], help="Formato (padrão: mxf).")
    group_output.add_argument("-d", "--duracao", type=int, default=180, help="Duração alvo em segundos.")
    
    group_extra = parser.add_argument_group("⚙️ Extras")
    group_extra.add_argument("--no-subs", action="store_true", help="Desativa legendas.")
    
    args = parser.parse_args()
    show_banner()
    
    if os.path.exists(args.input):
        processar_video(args.input, args.output_format, args.duracao, not args.no_subs, args.texto, args.prompt)
    else:
        console.print(f"[bold red]Erro: Arquivo '{args.input}' não encontrado.[/bold red]")
