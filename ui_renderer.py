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
        self.color_magenta = (255, 0, 255) # 클리어 이펙트를 위한 보라색 추가

    def draw_all(self, frame, state, round_info, left_finger, right_finger, trajectories, game_manager=None):
        self._draw_trajectories(frame, trajectories)

        if state == "WAITING":
            self._draw_waiting_screen(frame)
        elif state == "PLAYING":
            self._draw_playing_screen(frame, round_info, game_manager)
        elif state == "ROUND_CLEAR": # [추가됨] 라운드 전환 상태일 때
            self._draw_round_clear_screen(frame, round_info)
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

    def _draw_playing_screen(self, frame, round_info, game_manager):
        current_round, missions = round_info
        cv2.putText(frame, f"ROUND {current_round}", (550, 80), self.font, 1.5, self.color_yellow, 3)

        # [변경됨] 각 손의 독립적인 성공 횟수를 가져옵니다.
        left_count = game_manager.success_count['left'] if game_manager else 0
        right_count = game_manager.success_count['right'] if game_manager else 0

        cv2.putText(frame, f"Left Hand: {missions['left']} ({left_count}/3)", (50, 80), self.font, 1, self.color_red, 2)
        cv2.putText(frame, f"Right Hand: {missions['right']} ({right_count}/3)", (850, 80), self.font, 1, self.color_blue, 2)

        if game_manager:
            for hand in ["left", "right"]:
                ax, ay, ar = game_manager.anchors[hand]
                
                # [우선순위 변경]
                # 1순위: 현재 밖에서 그림을 그리고 있다면 무조건 빨간색 표시
                if game_manager.is_drawing[hand]:
                    color = self.color_red
                # 2순위: 그리지 않고 대기 중인데, 3번 이상 성공했다면 노란색 표시
                elif game_manager.success_count[hand] >= 3:
                    color = self.color_yellow
                # 3순위: 그 외의 일반적인 대기 상태는 초록색 표시
                else:
                    color = self.color_green
                    
                cv2.circle(frame, (ax, ay), ar, color, 4)
                cv2.circle(frame, (ax, ay), 5, color, -1) 
                cv2.putText(frame, "START", (ax - 30, ay - 70), self.font, 0.6, color, 2)
                
    def _draw_round_clear_screen(self, frame, round_info):
        """[추가됨] 라운드를 클리어했을 때 화면 한가운데에 크게 나타나는 효과"""
        current_round, _ = round_info
        cv2.putText(frame, f"ROUND {current_round} SUCCESS!", (250, 350), self.font, 2.5, self.color_magenta, 6)
        cv2.putText(frame, "Get ready for the next stage...", (400, 450), self.font, 1, self.color_white, 2)

    def _draw_cleared_screen(self, frame):
        cv2.putText(frame, "ALL MISSIONS CLEARED!", (250, 350), self.font, 2.5, self.color_green, 6)
        cv2.putText(frame, "You have a great Dual-Brain!", (400, 450), self.font, 1.5, self.color_white, 3)

    def _draw_trajectories(self, frame, trajectories):
        if len(trajectories['left']) > 1:
            pts_left = np.array(trajectories['left'], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_left], False, self.color_red, 5)

        if len(trajectories['right']) > 1:
            pts_right = np.array(trajectories['right'], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts_right], False, self.color_blue, 5)