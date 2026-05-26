"""
파일명: hand_tracker.py
설명: MediaPipe Hands API를 캡슐화(Encapsulation)하여 손가락 좌표 추적을 전담하는 모듈
복잡한 내부 동작을 숨기고, 외부에는 오직 '양손 검지손가락의 픽셀 좌표'라는 정제된 결과만 반환
"""

import cv2 as cv
import mediapipe as mp

class HandTracker:
    def __init__(self, max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils

    def get_index_fingers(self, frame, draw=True):
        # 입력된 BGR 이미지 프레임에서 양손 검지손가락 끝(Landmark 8) 좌표를 추출
        
        # MediaPipe는 RGB 포맷을 사용하므로, OpenCV 기본 포맷(BGR)을 변환
        img_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)
        
        left_finger, right_finger = None, None
        
        # 정규화된 비율 좌표(0~1)를 실제 픽셀 좌표로 변환하기 위해 화면 크기(w, h) 가져오기
        h, w, c = frame.shape

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, hand_info in zip(results.multi_hand_landmarks, results.multi_handedness):
                
                hand_label = hand_info.classification[0].label
                idx_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                # 비율 좌표에 가로/세로 길이를 곱해 정수형(int) 픽셀 좌표로 변환하기
                cx, cy = int(idx_tip.x * w), int(idx_tip.y * h)
                
                if hand_label == 'Left':
                    left_finger = (cx, cy)
                elif hand_label == 'Right':
                    right_finger = (cx, cy)

                # 디버깅 및 시각적 효과
                if draw:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    cv.circle(frame, (cx, cy), 15, (255, 0, 0), cv.FILLED)

        return left_finger, right_finger