"""
파일명: ui_renderer.py
설명: OpenCV를 이용하여 화면에 게임 UI(텍스트, 버튼, 손가락 궤적 등)를 그리는 역할을 전담하는 모듈입니다.
"""

import cv2
import numpy as np

class UIRenderer:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX 
        self.color_green = (0, 255, 0)
        self.color_red = (0, 0, 255)
        self.color_blue = (255, 0, 0)
        self.color_white = (255, 255, 255)
        self.color_yellow = (0, 255, 255)

    # [수정됨] 매개변수에 game_manager=None 이 추가되었습니다.
    def draw_all(self, frame, state, round_info, left_finger, right_finger, trajectories, game_manager=None):
        self._draw_trajectories(frame, trajectories)

        if state == "WAITING":
            self._draw_waiting_screen(frame)
        elif state == "PLAYING":
            # [수정됨] 플레이 화면을 그릴 때 game_manager를 같이 넘겨줍니다.
            self._draw_playing_screen(frame, round_info, game_manager)
        elif state == "CLEARED":
            self._draw_cleared_screen(frame)

        return frame

    def _draw_waiting_screen(self, frame):
        cv2.putText(frame, "SplitBrain Challenge", (300, 150), self.font, 2, self.color_yellow, 4)
        cv2.putText(frame, "Hover your fingers on START to play", (350, 220), self.font, 1, self.color_white, 2)

        box_pts = (540, 300) 
        box_pts2 = (740, 420) 
        cv2.rectangle(frame, box_pts, box_pts2, self.color_green, 3)
        cv2.putText(frame, "START", (585, 375), self.font, 1.5, self.color_green, 3)

    # 매개변수에 game_manager가 추가되었고, 앵커를 그리는 로직이 포함되었습니다.
    def _draw_playing_screen(self, frame, round_info, game_manager):
        current_round, missions = round_info

        cv2.putText(frame, f"ROUND {current_round}", (550, 80), self.font, 1.5, self.color_yellow, 3)
        cv2.putText(frame, f"Left Hand: {missions['left']}", (50, 80), self.font, 1, self.color_red, 2)
        cv2.putText(frame, f"Right Hand: {missions['right']}", (850, 80), self.font, 1, self.color_blue, 2)

        # 게임 매니저 정보가 전달되었다면, 화면 양쪽에 시작점(Anchor) 원을 그립니다.
        if game_manager:
            for hand in ["left", "right"]:
                ax, ay, ar = game_manager.anchors[hand]
                
                if game_manager.completed[hand]:
                    color = self.color_yellow
                elif game_manager.is_drawing[hand]:
                    color = self.color_red
                else:
                    color = self.color_green
                    
                cv2.circle(frame, (ax, ay), ar, color, 4)
                cv2.circle(frame, (ax, ay), 5, color, -1) 
                cv2.putText(frame, "START", (ax - 30, ay - 70), self.font, 0.6, color, 2)

    def _draw_cleared_screen(self, frame):
        cv2.putText(frame, "MISSION CLEARED!", (350, 350), self.font, 2.5, self.color_green, 5)
        cv2.putText(frame, "You have a great Dual-Brain!", (400, 450), self.font, 1, self.color_white, 2)

    def _draw_trajectories(self, frame, trajectories):
        if len(trajectories['left']) > 1:
            pts_left = np.array(trajectories['left'], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_left], False, self.color_red, 5)

        if len(trajectories['right']) > 1:
            pts_right = np.array(trajectories['right'], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_right], False, self.color_blue, 5)
    def _draw_playing_screen(self, frame, round_info, game_manager):
        current_round, missions = round_info

        cv2.putText(frame, f"ROUND {current_round}", (550, 80), self.font, 1.5, self.color_yellow, 3)

        # 게임 매니저에서 현재 성공 횟수를 가져옵니다. (안전장치 포함)
        success_count = game_manager.success_count if game_manager else 0

        # 미션 텍스트 뒤에 성공 횟수 (n/3)를 추가하여 출력합니다.
        cv2.putText(frame, f"Left Hand: {missions['left']} ({success_count}/3)", (50, 80), self.font, 1, self.color_red, 2)
        cv2.putText(frame, f"Right Hand: {missions['right']} ({success_count}/3)", (850, 80), self.font, 1, self.color_blue, 2)

        if game_manager:
            for hand in ["left", "right"]:
                ax, ay, ar = game_manager.anchors[hand]
                
                if game_manager.completed[hand]:
                    color = self.color_yellow
                elif game_manager.is_drawing[hand]:
                    color = self.color_red
                else:
                    color = self.color_green
                    
                cv2.circle(frame, (ax, ay), ar, color, 4)
                cv2.circle(frame, (ax, ay), 5, color, -1) 
                cv2.putText(frame, "START", (ax - 30, ay - 70), self.font, 0.6, color, 2)