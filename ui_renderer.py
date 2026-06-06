"""
파일명: ui_renderer.py
설명: OpenCV를 이용하여 화면에 UI 텍스트, 시작점, 궤적, 그리고 플레이어를 돕는 점선 가이드를 그리기, 성공한 도형 박제
"""

import cv2 as cv
import numpy as np
import math 

class UIRenderer:
    def __init__(self):
        # 폰트 둥글고 귀여운 스타일로 변경
        self.font = cv.FONT_HERSHEY_DUPLEX 
        
        # 파스텔톤
        self.color_green = (120, 220, 120)
        self.color_red = (100, 100, 255)    # 코랄빛 부드러운 레드
        self.color_blue = (250, 160, 80)    # 부드러운 스카이블루
        self.color_white = (250, 250, 250)
        self.color_yellow = (80, 210, 255)
        self.color_magenta = (210, 130, 240)
        
        # 배경색 (버튼용으로만 사용)
        self.color_bg_dark = (220, 230, 235)
        # timer 색상
        self.color_black = (30, 30, 30)
        # 테두리용 보색
        self.color_shadow = (255, 255, 255)

    # 텍스트를 화면 가로 중앙에 배치
    def _draw_centered_text(self, frame, text, y, font, scale, color, thickness, draw_bg=False):
        text_size = cv.getTextSize(text, font, scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        cv.putText(frame, text, (text_x, y), font, scale, color, thickness)

    # 텍스트에 보색 테두리 효과를 주는 함수
    def _draw_text_with_shadow(self, frame, text, x, y, font, scale, color, thickness, center=False):
        if center:
            text_size = cv.getTextSize(text, font, scale, thickness)[0]
            x = (frame.shape[1] - text_size[0]) // 2
        cv.putText(frame, text, (x, y + 2), font, scale, self.color_shadow, thickness + 2)
        cv.putText(frame, text, (x, y), font, scale, color, thickness)

    def _draw_dotted_line(self, frame, p1, p2, color, thickness=2, gap=15):
        # 두 점(p1, p2) 사이의 거리를 계산해 일정한 간격(gap)으로 원을 찍어 점선을 생성
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if dist == 0: return
        for d in np.arange(0, dist, gap):
            r = d / dist # 전체 거리 대비 현재 위치의 비율
            x = int(p1[0] * (1 - r) + p2[0] * r)
            y = int(p1[1] * (1 - r) + p2[1] * r)
            cv.circle(frame, (x, y), thickness, color, -1)

    def _draw_guide_shape(self, frame, shape, cx, cy, hand):
        # 시작점(cx, cy)을 첫 번째 꼭짓점으로 삼아, 시원시원한 3배 크기의 하얀색 점선 가이드 그리기
        color = self.color_white
        # 양손의 궤적이 화면 밖으로 나가지 않도록 다각형을 그릴 때 거울처럼 대칭(dir) 적용
        dir = 1 if hand == "left" else -1
        
        # 주의: 여기 조건문(shape)은 게임 매니저에서 넘어오는 영단어와 완벽하게 일치해야 함
        if shape == "Horizontal":
            # 시작점에서  왼쪽 방향 300px
            self._draw_dotted_line(frame, (cx, cy), (cx - 300, cy), color)
            
        elif shape == "Vertical":
            # 시작점에서 아래로 일직선 300px
            self._draw_dotted_line(frame, (cx, cy), (cx, cy + 300), color)
            
        elif shape == "Triangle":
            # 시작점이 삼각형의 맨 위 꼭짓점이 되도록 계산
            p1 = (cx, cy)
            p2 = (cx - 160, cy + 280)
            p3 = (cx + 160, cy + 280)
            self._draw_dotted_line(frame, p1, p2, color)
            self._draw_dotted_line(frame, p2, p3, color)
            self._draw_dotted_line(frame, p3, p1, color)
            
        elif shape == "Square":
            # 시작점이 사각형의 상단 꼭짓점(안쪽 방향)
            p1 = (cx, cy)
            p2 = (cx + dir * 250, cy)
            p3 = (cx + dir * 250, cy + 250)
            p4 = (cx, cy + 250)
            self._draw_dotted_line(frame, p1, p2, color)
            self._draw_dotted_line(frame, p2, p3, color)
            self._draw_dotted_line(frame, p3, p4, color)
            self._draw_dotted_line(frame, p4, p1, color)
            
        elif shape == "Pentagon":
            # 중심을 아래로(cy + 160) 이동시켜, 오각형의 맨 위 꼭짓점이 앵커의 정중앙에 딱 맞도록 수학적으로 계산
            pts = []
            for i in range(5):
                angle = math.radians(270 + i * 72)
                x = cx + int(160 * math.cos(angle))
                y = cy + 160 + int(160 * math.sin(angle)) 
                pts.append((x, y))
            for i in range(5):
                self._draw_dotted_line(frame, pts[i], pts[(i+1)%5], color)

    # 사용자가 직접 그린 삐뚤빼뚤한 궤적 축소하여 박제하는 함수
    def _draw_user_mini_shape(self, frame, pts, cx, cy, color, size=30):
        if not pts or len(pts) < 2: return
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        orig_cx, orig_cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        max_dim = max(width, height) if max(width, height) > 0 else 1
        scale = (size * 2) / max_dim
        scaled_pts = [[int((p[0] - orig_cx) * scale + cx), int((p[1] - orig_cy) * scale + cy)] for p in pts]
        cv.polylines(frame, [np.array(scaled_pts, np.int32).reshape((-1, 1, 2))], False, color, 3)

    # 타이머, RESTART, QUIT 버튼을 항시 띄워주는 HUD
    def _draw_hud(self, frame, game_manager):
        if not game_manager or game_manager.state == "WAITING": return
        # RESTART(좌측 하단)와 QUIT(우측 하단) 버튼 그리기
        for b_box, text, col, h_val in [(game_manager.restart_button_box, "RESTART", self.color_red, game_manager.restart_hover_frames), 
                                        (game_manager.quit_button_box, "QUIT", self.color_magenta, game_manager.quit_hover_frames)]:
            cv.rectangle(frame, (b_box[0], b_box[1]), (b_box[2], b_box[3]), self.color_bg_dark, -1)
            cv.rectangle(frame, (b_box[0], b_box[1]), (b_box[2], b_box[3]), col, 3)
            tw, th = cv.getTextSize(text, self.font, 0.7, 2)[0]
            if h_val > 0:
                fill_w = int((b_box[2]-b_box[0]) * (h_val / 30.0))
                cv.rectangle(frame, (b_box[0], b_box[1]), (b_box[0] + fill_w, b_box[3]), col, -1)
                cv.putText(frame, text, (b_box[0]+(b_box[2]-b_box[0]-tw)//2, b_box[1]+(b_box[3]-b_box[1]+th)//2), self.font, 0.7, self.color_white, 2)
            else:
                cv.putText(frame, text, (b_box[0]+(b_box[2]-b_box[0]-tw)//2, b_box[1]+(b_box[3]-b_box[1]+th)//2), self.font, 0.7, col, 2)
        
        # 타이머/최고기록 중앙 정렬 및 아래로 한 칸 이동 (y=70/120)
        cur, best = game_manager.get_time_info()
        self._draw_text_with_shadow(frame, f"TIME: {cur:.1f}s", 0, 70, self.font, 1.2, self.color_black, 3, center=True)
        self._draw_text_with_shadow(frame, f"BEST: {best:.1f}s" if best != float('inf') else "BEST: --", 0, 120, self.font, 0.9, self.color_black, 3, center=True)

    def draw_all(self, frame, state, round_info, left_finger, right_finger, trajectories, game_manager=None):
        # 게임의 현재 State에 맞추어 적절한 UI 화면을 렌더링
        self._draw_trajectories(frame, trajectories)
        if state == "WAITING": self._draw_waiting_screen(frame, game_manager)
        elif state == "PLAYING": self._draw_playing_screen(frame, round_info, game_manager)
        elif state == "ROUND_CLEAR": self._draw_round_clear_screen(frame, round_info)
        elif state == "CLEARED": self._draw_cleared_screen(frame)
        self._draw_hud(frame, game_manager) 
        return frame

    def _draw_waiting_screen(self, frame, game_manager):
        # 타이틀 중앙 정렬 및 세로 위치 조정
        self._draw_text_with_shadow(frame, "SplitBrain Challenge", 0, 180, self.font, 1.7, self.color_yellow, 5, center=True)
        self._draw_centered_text(frame, "Hover your fingers on START to play", 260, self.font, 1, self.color_white, 2)
        box_w, box_h, bx, by = 200, 120, 540, 330
        # START 버튼 게이지 적용
        fill_w = int(box_w * (game_manager.hover_frames / 30.0))
        cv.rectangle(frame, (bx, by), (bx+fill_w, by+box_h), self.color_green, -1)
        cv.rectangle(frame, (bx, by), (bx+box_w, by+box_h), self.color_green, 4)
        tw, th = cv.getTextSize("START", self.font, 1.5, 3)[0]
        cv.putText(frame, "START", (bx+(box_w-tw)//2, by+(box_h+th)//2), self.font, 1.5, self.color_white, 3)

    def _draw_playing_screen(self, frame, round_info, game_manager):
        current_round, missions = round_info
        # ROUND 중앙 정렬 및 아래로 이동
        r_text = f"ROUND {current_round}"
        self._draw_text_with_shadow(frame, r_text, 0, 210, self.font, 1.7, self.color_yellow, 5, center=True)
        
        # Left/Right 문구 및 요소들 1칸 밑으로(y=110) 이동
        left_count, right_count = game_manager.success_count['left'], game_manager.success_count['right']
        self._draw_text_with_shadow(frame, f"Left: {missions['left']} ({left_count}/3)", 50, 110, self.font, 0.9, self.color_red, 2)
        self._draw_text_with_shadow(frame, f"Right: {missions['right']} ({right_count}/3)", 850, 110, self.font, 0.9, self.color_blue, 2)

        for i in range(left_count): self._draw_user_mini_shape(frame, game_manager.success_shapes['left'][i], 80 + (i%3)*60, 160 + (i//3)*60, self.color_red, size=30)
        for i in range(right_count): self._draw_user_mini_shape(frame, game_manager.success_shapes['right'][i], 880 + (i%3)*60, 160 + (i//3)*60, self.color_blue, size=30)
        
        #  앵커와 START 텍스트도 1칸 밑으로 이동
        if game_manager:
            for hand in ["left", "right"]:
                ax, ay, ar = game_manager.anchors[hand]
                ay += 30 # 한 칸 밑으로
                color = self.color_red if game_manager.is_drawing[hand] else (self.color_blue if hand == 'right' else self.color_green)
                if game_manager.success_count[hand] == 0: self._draw_guide_shape(frame, missions[hand], ax, ay, color)
                cv.circle(frame, (ax, ay), ar, color, 4)
                cv.circle(frame, (ax, ay), 5, color, -1) 
                cv.putText(frame, "START", (ax - 30, ay - 55), self.font, 0.9, color, 2)

    def _draw_round_clear_screen(self, frame, round_info):
        self._draw_centered_text(frame, f"ROUND {round_info[0]} SUCCESS!", 350, self.font, 2.5, self.color_magenta, 6, False)
        self._draw_centered_text(frame, "Get ready for the next stage...", 450, self.font, 1, self.color_white, 2)

    def _draw_cleared_screen(self, frame):
        self._draw_centered_text(frame, "ALL MISSIONS CLEARED!", 350, self.font, 3.0, self.color_green, 6, False)
        self._draw_centered_text(frame, "You have a great Dual-Brain!", 450, self.font, 1.5, self.color_white, 3)

    def _draw_trajectories(self, frame, trajectories):
        for hand, col in [('left', self.color_red), ('right', self.color_blue)]:
            if len(trajectories[hand]) > 1:
                pts = np.array(trajectories[hand], np.int32).reshape((-1, 1, 2))
                cv.polylines(frame, [pts], False, col, 5)