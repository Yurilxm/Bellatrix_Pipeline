import cv2
import numpy as np

class DetectorFadesPretos:
    def __init__(self, video_path, threshold=30, fps=29.97):
        self.video_path = video_path
        self.threshold = threshold
        self.fps = fps
        self.tempos_inicio = []
        self.tempos_fim = []

    def is_black_frame(self, frame):
        return np.all(frame < self.threshold)

    def detectar(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Erro: Não foi possível abrir o vídeo {self.video_path}")

        inicio_fade = None
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            tempo_atual = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            if self.is_black_frame(frame):
                if inicio_fade is None:
                    inicio_fade = tempo_atual
            else:
                if inicio_fade is not None:
                    # Só considera fades com duração maior que 0.5s (evita piscadas)
                    if (tempo_atual - inicio_fade) > 0.5:
                        self.tempos_inicio.append(inicio_fade)
                        self.tempos_fim.append(tempo_atual)
                    inicio_fade = None
        cap.release()
        
        # Retorna os blocos de vídeo (entre as fades)
        blocos = []
        for i in range(len(self.tempos_fim) - 1):
            inicio_bloco = self.tempos_fim[i]
            fim_bloco = self.tempos_inicio[i+1]
            if (fim_bloco - inicio_bloco) > 2.0: # Ignora blocos muito curtos
                blocos.append((inicio_bloco, fim_bloco))
        return blocos
