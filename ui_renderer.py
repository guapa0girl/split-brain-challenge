"""
파일명: ui_renderer.py
설명: OpenCV를 이용하여 화면에 게임 UI(텍스트, 버튼, 손가락 궤적 등)를 그리는 역할을 전담하는 모듈입니다.
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
        text_size = cv.getTextSize(text, font, scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        cv.putText(frame, text, (text_x, y), font, scale, color, thickness)

    def _draw_dotted_line(self, frame, p1, p2, color, thickness=2, gap=15):
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if dist == 0: return
        for d in np.arange(0, dist, gap):
            r = d / dist
            x = int(p1[0] * (1 - r) + p2[0] * r)
            y = int(p1[1] * (1 - r) + p2[1] * r)
            cv.circle(frame, (x, y), thickness, color, -1)

    # 점선 크기 3배 증가 및 시작점(cx, cy)이 무조건 꼭짓점이 됩니다.
    def _draw_guide_shape(self, frame, shape, cx, cy, hand):
        color = self.color_white
        # 오른손이 화면 밖으로 나가는 것을 막기 위해 가로 방향을 거울처럼 대칭(-1)으로 만듭니다.
        dir = 1 if hand == "left" else -1
        
        if shape == "Horizontal":
            # 시작점에서 가로로 350px (왼손은 오른쪽으로, 오른손은 왼쪽으로)
            self._draw_dotted_line(frame, (cx, cy), (cx + dir * 350, cy), color)
            
        elif shape == "Vertical":
            # 시작점에서 아래로 350px
            self._draw_dotted_line(frame, (cx, cy), (cx, cy + 350), color)
            
        elif shape == "Triangle":
            # 시작점(cx, cy)이 삼각형의 맨 위 꼭짓점
            p1 = (cx, cy)
            p2 = (cx - 160, cy + 280)
            p3 = (cx + 160, cy + 280)
            self._draw_dotted_line(frame, p1, p2, color)
            self._draw_dotted_line(frame, p2, p3, color)
            self._draw_dotted_line(frame, p3, p1, color)
            
        elif shape == "Square":
            # 시작점(cx, cy)이 사각형의 상단 꼭짓점
            p1 = (cx, cy)
            p2 = (cx + dir * 250, cy)
            p3 = (cx + dir * 250, cy + 250)
            p4 = (cx, cy + 250)
            self._draw_dotted_line(frame, p1, p2, color)
            self._draw_dotted_line(frame, p2, p3, color)
            self._draw_dotted_line(frame, p3, p4, color)
            self._draw_dotted_line(frame, p4, p1, color)
            
        elif shape == "Pentagon":
            # 시작점(cx, cy)이 오각형의 맨 위 꼭짓점
            # 도형 중심의 y좌표를 반지름(160)만큼 내려서 맨 위가 시작점과 일치하도록 계산
            pts = []
            for i in range(5):
                angle = math.radians(270 + i * 72)
                x = cx + int(160 * math.cos(angle))
                y = cy + 160 + int(160 * math.sin(angle)) # 중심을 cy + 160으로 이동
                pts.append((x, y))
            for i in range(5):
                self._draw_dotted_line(frame, pts[i], pts[(i+1)%5], color)

    def draw_all(self, frame, state, round_info, left_finger, right_finger, trajectories, game_manager=None):
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
        box_x = 540 
        box_y = 300
        cv.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), self.color_green, 3)
        
        text = "START"
        text_size = cv.getTextSize(text, self.font, 1.5, 3)[0]
        text_x = box_x + (box_w - text_size[0]) // 2
        text_y = box_y + (box_h + text_size[1]) // 2
        cv.putText(frame, text, (text_x, text_y), self.font, 1.5, self.color_green, 3)

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
                
                # [수정됨] hand 변수를 함께 넘겨줍니다.
                if game_manager.success_count[hand] == 0:
                    self._draw_guide_shape(frame, missions[hand], ax, ay, hand)

                if game_manager.is_drawing[hand]:
                    color = self.color_red
                elif game_manager.success_count[hand] >= 3:
                    color = self.color_yellow
                else:
                    color = self.color_green
                    
                cv.circle(frame, (ax, ay), ar, color, 4)
                cv.circle(frame, (ax, ay), 5, color, -1) 
                
                st_size = cv.getTextSize("START", self.font, 0.6, 2)[0]
                cv.putText(frame, "START", (ax - st_size[0]//2, ay - 55), self.font, 0.6, color, 2)

    def _draw_round_clear_screen(self, frame, round_info):
        current_round, _ = round_info
        self._draw_centered_text(frame, f"ROUND {current_round} SUCCESS!", 350, self.font, 2.5, self.color_magenta, 6)
        self._draw_centered_text(frame, "Get ready for the next stage...", 450, self.font, 1, self.color_white, 2)

    def _draw_cleared_screen(self, frame):
        self._draw_centered_text(frame, "ALL MISSIONS CLEARED!", 350, self.font, 2.5, self.color_green, 6)
        self._draw_centered_text(frame, "You have a great Dual-Brain!", 450, self.font, 1.5, self.color_white, 3)

    def _draw_trajectories(self, frame, trajectories):
        if len(trajectories['left']) > 1:
            pts_left = np.array(trajectories['left'], np.int32).reshape((-1, 1, 2))
            cv.polylines(frame, [pts_left], False, self.color_red, 5)

        if len(trajectories['right']) > 1:
            pts_right = np.array(trajectories['right'], np.int32).reshape((-1, 1, 2))
            cv.polylines(frame, [pts_right], False, self.color_blue, 5)