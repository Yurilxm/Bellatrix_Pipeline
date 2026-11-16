import os
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

def processar_video(input_path, output_format="mp4", duracao_alvo=180, gerar_legenda=True):
    # (Mesma lógica de processamento de antes, mas usando console.print para ficar bonito)
    console.print(f"\n[bold cyan]🚀 Iniciando Pipeline para:[/bold cyan] [white]{input_path}[/white]")
    
    # 0. Validação
    console.print("[yellow]⏳ [0/5] Validando integridade do vídeo...[/yellow]")
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        console.print(f"[bold red]❌ Vídeo inválido: {mensagem}[/bold red]")
        return
    console.print(f"[green]✅ {mensagem}[/green]")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = "temp_cortes"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 1. Detecção Visual
    console.print("[yellow]⏳ [1/5] Detectando blocos (fades)...[/yellow]")
    detector = DetectorFadesPretos(input_path)
    blocos = detector.detectar()
    console.print(f"[green]✅ {len(blocos)} blocos encontrados.[/green]")
    
    if not blocos:
        console.print("[bold red]❌ Nenhum bloco válido encontrado. Abortando.[/bold red]")
        return

    # 2. Transcrição
    console.print("[yellow]⏳ [2/5] Transcrevendo áudio (Whisper)...[/yellow]")
    srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
    transcrever_e_gerar_srt(input_path, srt_temp)
    console.print("[green]✅ Transcrição concluída.[/green]")
    
    # 3. Decisão Editorial
    console.print("[yellow]⏳ [3/5] Selecionando melhores trechos (LLM)...[/yellow]")
    trechos_escolhidos = analisar_e_selecionar(blocos, srt_temp, duracao_alvo)
    console.print(f"[green]✅ {len(trechos_escolhidos)} trechos selecionados.[/green]")
    
    # 4. Corte e Montagem
    console.print("[yellow]⏳ [4/5] Cortando e renderizando vídeo final...[/yellow]")
    cortes_gerados = []
    for i, trecho in enumerate(trechos_escolhidos):
        output_corte = os.path.join(temp_dir, f"corte_{i}.{output_format}")
        cortar_video(input_path, output_corte, trecho["start"], trecho["end"], output_format)
        cortes_gerados.append(output_corte)
        
    video_final = gerar_nome_final(input_path, os.getcwd())
    if len(cortes_gerados) > 1:
        juntar_videos(cortes_gerados, video_final)
    else:
        shutil.move(cortes_gerados[0], video_final)
    console.print("[green]✅ Montagem concluída.[/green]")

    # 5. Legendas (Burn-in)
    if gerar_legenda:
        console.print("[yellow]⏳ [5/5] Aplicando legendas no vídeo final...[/yellow]")
        video_com_legenda = video_final.replace(f".{output_format}", f"_legendado.{output_format}")
        embutir_legenda(video_final, srt_temp, video_com_legenda)
        if os.path.exists(video_final): os.remove(video_final)
        video_final = video_com_legenda
        console.print("[green]✅ Legendas aplicadas.[/green]")

    # Limpeza
    shutil.rmtree(temp_dir)
    
    console.print(f"\n[bold green]🎉 Pipeline finalizada![/bold green] Arquivo salvo como: [cyan]{video_final}[/cyan]\n")

def show_banner():
    banner = Text()
    banner.append("⚡ ", style="bold yellow")
    banner.append("BELLATRIX PIPELINE", style="bold cyan")
    banner.append(" (Edição Automatizada com IA)\n", style="bold white")
    banner.append("Unindo Bellatrix + Sirius + Nano + Whisper + LLaMA", style="dim italic")
    console.print(Panel.fit(banner, border_style="cyan"))

if __name__ == "__main__":
    # Cria o parser usando o RichHelpFormatter
    parser = argparse.ArgumentParser(
        description="Microserviço de Edição Automatizada de Vídeo para TV.",
        epilog="Exemplo:\n  python main.py -i video.mp4 -d 180 -o mp4",
        formatter_class=RichHelpFormatter
    )
    
    # Agrupando os argumentos para ficar organizado (como no Jarvis)
    group_input = parser.add_argument_group("📥 Entrada")
    group_input.add_argument("-i", "--input", required=True, help="Caminho completo do vídeo de entrada.")

    group_output = parser.add_argument_group("📤 Saída")
    group_output.add_argument("-o", "--output_format", default="mp4", choices=["mp4", "mxf", "mov", "mkv"], help="Formato de saída (padrão: mp4). Use 'mxf' para broadcast.")
    group_output.add_argument("-d", "--duracao", type=int, default=180, help="Duração alvo em segundos (padrão: 180).")
    
    group_extra = parser.add_argument_group("⚙️ Configurações Extras")
    group_extra.add_argument("--no-subs", action="store_true", help="Desativa a geração de legendas no vídeo final.")
    
    args = parser.parse_args()
    
    show_banner()
    
    if os.path.exists(args.input):
        processar_video(args.input, args.output_format, args.duracao, not args.no_subs)
    else:
        console.print(f"[bold red]Erro: Arquivo '{args.input}' não encontrado.[/bold red]")
