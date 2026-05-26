"""
파일명: hand_tracker.py
설명: MediaPipe Hands API를 캡슐화(Encapsulation)하여 손가락 좌표 추적을 전담하는 모듈로
복잡한 MediaPipe의 내부 동작이나 랜드마크 추출 로직을 이 클래스 내부로 숨기고, 
외부(main.py)에는 오직 '양손 검지손가락의 (x, y) 픽셀 좌표'라는 정제된 결과만 반환합니다.
이를 통해 객체 간의 결합도를 낮추고 유지보수성을 높입니다.
"""

import cv2 as cv
import mediapipe as mp

class HandTracker:
    def __init__(self, max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7):
        """
        HandTracker 클래스의 생성자입니다.
        객체가 생성될 때 MediaPipe Hands 모델을 초기화하여 메모리에 로드합니다.
        
        :param max_num_hands: 화면에서 추적할 최대 손의 개수 (양손이므로 2로 설정)
        :param min_detection_confidence: 손을 처음 감지할 때의 신뢰도 임계값 (0.0 ~ 1.0)
        :param min_tracking_confidence: 감지된 손을 계속 추적할 때의 신뢰도 임계값
        """
        # MediaPipe의 손 추적 모듈을 불러옵니다.
        self.mp_hands = mp.solutions.hands
        
        # 실제 손 추적을 수행할 객체를 생성하고 설정값을 전달합니다.
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # (선택 사항) 화면에 랜드마크를 그리기 위한 도구 모듈을 불러옵니다.
        # 디버깅이나 테스트 용도로 유용하게 사용할 수 있습니다.
        self.mp_draw = mp.solutions.drawing_utils

    def get_index_fingers(self, frame, draw=True):
        """
        입력된 이미지 프레임에서 양손의 검지손가락 끝(Landmark 8) 좌표를 추출합니다.
        
        :param frame: 웹캠으로부터 읽어들인 BGR 이미지 프레임 (main.py에서 전달됨)
        :param draw: 프레임 위에 랜드마크와 연결선을 그릴지 여부 (디버깅용)
        :return: (left_finger, right_finger) 형태의 튜플 반환
                 각 손가락 좌표는 (x, y) 형태의 튜플이며, 인식되지 않은 손은 None을 반환합니다.
        """
        
        # MediaPipe는 RGB 포맷의 이미지를 사용하므로, OpenCV의 기본 포맷인 BGR을 RGB로 변환합니다.
        img_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        
        # 변환된 이미지를 모델에 통과시켜 손의 위치와 랜드마크를 처리(process)합니다.
        results = self.hands.process(img_rgb)
        
        # 반환할 좌/우 검지손가락 좌표 변수를 None으로 초기화합니다.
        left_finger = None
        right_finger = None
        
        # 이미지의 실제 가로(w), 세로(h) 픽셀 크기를 가져옵니다. 
        # (MediaPipe는 0~1 사이의 정규화된 비율 좌표를 반환하므로 픽셀 좌표로 변환하기 위해 필요합니다)
        h, w, c = frame.shape

        # 화면에서 손이 하나라도 감지되었는지 확인합니다.
        if results.multi_hand_landmarks and results.multi_handedness:
            
            # 감지된 모든 손(최대 2개)에 대해 반복문을 실행합니다.
            # hand_landmarks: 해당 손의 21개 관절 좌표 데이터
            # hand_info: 해당 손이 왼손인지 오른손인지에 대한 정보
            for hand_landmarks, hand_info in zip(results.multi_hand_landmarks, results.multi_handedness):
                
                # 감지된 손이 'Left'인지 'Right'인지 문자열로 가져옵니다.
                # (참고: main.py에서 cv2.flip으로 화면을 반전시켰기 때문에 직관적인 방향과 일치하게 나옵니다)
                hand_label = hand_info.classification[0].label
                
                # 21개의 관절(Landmark) 중 8번 인덱스가 '검지손가락 끝(Index Finger Tip)'입니다.
                index_finger_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                # 정규화된 비율(0.0 ~ 1.0) 좌표에 실제 화면 크기(w, h)를 곱하여 픽셀(Pixel) 좌표로 변환합니다.
                # 픽셀 좌표는 정수(int)여야 하므로 int()로 감싸줍니다.
                cx, cy = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                
                # 손의 방향(Left/Right)에 따라 해당하는 변수에 좌표를 저장합니다.
                if hand_label == 'Left':
                    left_finger = (cx, cy)
                elif hand_label == 'Right':
                    right_finger = (cx, cy)

                # draw 옵션이 True일 경우, 현재 프레임 위에 관절 포인트와 뼈대 연결선을 시각적으로 그려줍니다.
                if draw:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    # 검지손가락 끝부분에만 시각적으로 눈에 띄도록 파란색 원을 추가로 그립니다.
                    cv.circle(frame, (cx, cy), 15, (255, 0, 0), cv.FILLED)

        # 최종적으로 추출된 양손 검지손가락의 픽셀 좌표를 반환합니다. 
        # 만약 한쪽 손만 화면에 있다면 다른 쪽은 None이 반환됩니다.
        return left_finger, right_finger