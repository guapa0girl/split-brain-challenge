"""
파일명: ui_renderer.py
설명: OpenCV를 이용하여 화면에 UI 텍스트, 시작점, 궤적, 그리고 플레이어를 돕는 점선 가이드를 그리기
"""

import cv2 as cv
import numpy as np
import math 

class UIRenderer:
    def __init__(self):
        self.font = cv.FONT_HERSHEY_SIMPLEX 
        self.color_green = (0, 255, 0)
        self.color_red = (0, 0, 255)
        self.color_blue = (255, 0, 0)
        self.color_white = (255, 255, 255)
        self.color_yellow = (0, 255, 255)
        self.color_magenta = (255, 0, 255)

    def _draw_centered_text(self, frame, text, y, font, scale, color, thickness):
        # 텍스트의 실제 픽셀 길이를 계산하여 화면 가로축 정중앙에 정렬
        text_size = cv.getTextSize(text, font, scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        cv.putText(frame, text, (text_x, y), font, scale, color, thickness)

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
        # [UX 향상] 양손의 궤적이 화면 밖으로 나가지 않도록 다각형을 그릴 때 거울처럼 대칭(dir) 적용
        dir = 1 if hand == "left" else -1
        
        # 주의: 여기 조건문(shape)은 게임 매니저에서 넘어오는 영단어와 완벽하게 일치해야 함
        if shape == "Horizontal":
            # 1라운드 가로선: 왼손은 왼쪽(-), 오른손은 오른쪽(+)으로 시원하게 뻗어나가도록 방향 반전
            h_dir = -1 if hand == "left" else 1
            self._draw_dotted_line(frame, (cx, cy), (cx + h_dir * 350, cy), color)
            
        elif shape == "Vertical":
            # 시작점에서 아래로 일직선 350px
            self._draw_dotted_line(frame, (cx, cy), (cx, cy + 350), color)
            
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

    def draw_all(self, frame, state, round_info, left_finger, right_finger, trajectories, game_manager=None):
        # 게임의 현재 State에 맞추어 적절한 UI 화면을 렌더링
        self._draw_trajectories(frame, trajectories)

        if state == "WAITING":
            self._draw_waiting_screen(frame)
        elif state == "PLAYING":
            self._draw_playing_screen(frame, round_info, game_manager)
        elif state == "ROUND_CLEAR":
            self._draw_round_clear_screen(frame, round_info)
        elif state == "CLEARED":
            self._draw_cleared_screen(frame)

        return frame

    def _draw_waiting_screen(self, frame):
        self._draw_centered_text(frame, "SplitBrain Challenge", 150, self.font, 2, self.color_yellow, 4)
        self._draw_centered_text(frame, "Hover your fingers on START to play", 220, self.font, 1, self.color_white, 2)
        
        box_w, box_h = 200, 120
        box_x, box_y = 540, 300
        cv.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), self.color_green, 3)
        
        # 버튼 안의 텍스트도 비율에 맞추어 중앙 정렬
        text_size = cv.getTextSize("START", self.font, 1.5, 3)[0]
        text_x = box_x + (box_w - text_size[0]) // 2
        text_y = box_y + (box_h + text_size[1]) // 2
        cv.putText(frame, "START", (text_x, text_y), self.font, 1.5, self.color_green, 3)

    def _draw_playing_screen(self, frame, round_info, game_manager):
        current_round, missions = round_info
        self._draw_centered_text(frame, f"ROUND {current_round}", 80, self.font, 1.5, self.color_yellow, 3)

        left_count = game_manager.success_count['left'] if game_manager else 0
        right_count = game_manager.success_count['right'] if game_manager else 0

        cv.putText(frame, f"Left Hand: {missions['left']} ({left_count}/3)", (50, 80), self.font, 1, self.color_red, 2)
        cv.putText(frame, f"Right Hand: {missions['right']} ({right_count}/3)", (850, 80), self.font, 1, self.color_blue, 2)

        if game_manager:
            for hand in ["left", "right"]:
                ax, ay, ar = game_manager.anchors[hand]
                
                # 아직 단 한 번도 성공하지 못했을 때(첫 번째 도형 그리기 전)만 하얀색 점선 가이드 띄우기
                if game_manager.success_count[hand] == 0:
                    self._draw_guide_shape(frame, missions[hand], ax, ay, hand)

                # 현재 상태에 따른 앵커 색상 우선순위
                if game_manager.is_drawing[hand]:
                    color = self.color_red     # 그림 그리는 중 (빨강)
                elif game_manager.success_count[hand] >= 3:
                    color = self.color_yellow  # 목표 달성 후 대기 (노랑)
                else:
                    color = self.color_green   # 일반 대기 상태 (초록)
                    
                cv.circle(frame, (ax, ay), ar, color, 4)
                cv.circle(frame, (ax, ay), 5, color, -1) 
                
                # 앵커 위 START 텍스트 미세 정렬
                st_size = cv.getTextSize("START", self.font, 0.6, 2)[0]
                cv.putText(frame, "START", (ax - st_size[0]//2, ay - 55), self.font, 0.6, color, 2)

    def _draw_round_clear_screen(self, frame, round_info):
        current_round, _ = round_info
        self._draw_centered_text(frame, f"ROUND {current_round} SUCCESS!", 350, self.font, 2.5, self.color_magenta, 6)
        self._draw_centered_text(frame, "Get ready for the next stage...", 450, self.font, 1, self.color_white, 2)

    def _draw_cleared_screen(self, frame):
        self._draw_centered_text(frame, "ALL MISSIONS CLEARED!", 350, self.font, 3.0, self.color_green, 6)
        self._draw_centered_text(frame, "You have a great Dual-Brain!", 450, self.font, 1.5, self.color_white, 3)

    def _draw_trajectories(self, frame, trajectories):
        # 누적된 궤적(배열)들을 폴리곤으로 이어 화면에 실제로 보여주는 역할
        if len(trajectories['left']) > 1:
            pts_left = np.array(trajectories['left'], np.int32).reshape((-1, 1, 2))
            cv.polylines(frame, [pts_left], False, self.color_red, 5)

        if len(trajectories['right']) > 1:
            pts_right = np.array(trajectories['right'], np.int32).reshape((-1, 1, 2))
            cv.polylines(frame, [pts_right], False, self.color_blue, 5)