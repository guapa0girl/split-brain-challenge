"""
파일명: shape_recognizer.py
설명: 사용자의 손가락 움직임(궤적) 좌표를 누적하고, 이 좌표들을 수학적으로 분석하여 어떤 도형(직선, 다각형 등)인지 판별하는 모듈로
      단순히 좌표만 잇는 것이 아니라, 사용자의 손떨림 노이즈를 제거(Convex Hull)하고 
      의도치 않은 꼼수(너무 작은 도형 그리기, 비율이 맞지 않는 선 긋기 등)를 방지하는 엄격한 평가 알고리즘이 포함되어 있습니다.
"""
import cv2 as cv
import numpy as np

class ShapeRecognizer:
    def __init__(self):
        """
        ShapeRecognizer 클래스 생성자입니다.
        양손의 궤적을 독립적으로 저장할 수 있도록 딕셔너리를 초기화합니다.
        """
        # 'left'와 'right' 키를 가지며, 각각 (x, y) 좌표 튜플들이 담길 빈 리스트를 생성합니다.
        self.trajectories = {'left': [], 'right': []}

    def get_trajectories(self):
        """
        현재까지 누적된 양손의 궤적 좌표 데이터를 반환합니다.
        주로 ui_renderer에서 화면에 실시간으로 선을 그릴 때 호출하여 사용합니다.
        """
        return self.trajectories

    def clear_trajectory(self, hand):
        """
        특정 손('left' 또는 'right')의 궤적 데이터를 초기화(삭제)합니다.
        도형 그리기에 성공했거나, 실패 후 다시 그려야 할 때 호출됩니다.
        """
        self.trajectories[hand] = []

    def add_point(self, hand, point):
        """
        손가락이 시작점(앵커) 밖으로 나가 그림을 그리는 동안, 
        매 프레임마다 인식된 손가락의 (x, y) 좌표를 궤적 리스트에 추가합니다.
        
        :param hand: 'left' 또는 'right' (어느 손인지)
        :param point: 인식된 손가락 끝 좌표 (x, y)
        """
        if point: # 좌표 값이 None이 아닐 때만(손이 화면에 보일 때만) 추가
            self.trajectories[hand].append(point)

    def evaluate_strict_shape(self, hand, target_shape):
        """
        궤적이 시작점으로 돌아왔을 때 단 한 번 호출되어, 지금까지 그린 궤적이 
        현재 미션(target_shape)과 정확히 일치하는지 엄격하게 판별합니다.
        
        :param hand: 'left' 또는 'right'
        :param target_shape: 현재 라운드의 목표 도형 (예: "Horizontal", "Triangle" 등)
        :return: 판별된 도형 이름 또는 실패 시 "Fail" 문자열 반환
        """
        points = self.trajectories[hand]
        
        # [예외 처리] 그려진 점의 개수가 15개 미만이면 의미 있는 도형으로 보기 어려우므로 무시합니다.
        # (실수로 앵커를 살짝 벗어났다가 바로 들어오는 오작동 방지)
        if len(points) < 15: 
            return "Fail"

        # 점들의 X좌표와 Y좌표를 각각 분리하여 리스트로 만듭니다.
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # 그려진 전체 궤적을 감싸는 가상의 경계 상자(Bounding Box)의 가로(dx), 세로(dy) 길이를 구합니다.
        dx = max(x_coords) - min(x_coords)
        dy = max(y_coords) - min(y_coords)

        # [1라운드] 직선 꼼수 방지 로직
        # 가로선(Horizontal) 판별: 가로 이동 거리(dx)가 최소 150픽셀 이상이어야 하며, 
        # 위아래 흔들림(dy)이 가로 길이의 절반(50%)보다 작아야만 가로선으로 인정합니다.
        if target_shape == "Horizontal":
            if dx > 150 and dy < (dx * 0.5): 
                return "Horizontal"
            return "Fail" # 조건에 맞지 않으면 즉시 실패 처리
            
        # 세로선(Vertical) 판별: 세로 이동 거리(dy)가 최소 150픽셀 이상이어야 하며, 
        # 좌우 흔들림(dx)이 세로 길이의 절반(50%)보다 작아야만 세로선으로 인정합니다.
        if target_shape == "Vertical":
            if dy > 150 and dx < (dy * 0.5): 
                return "Vertical"
            return "Fail"

        # [2, 3라운드] 다각형 꼼수 방지 로직
        # 파이썬의 리스트 형태인 points를 OpenCV 함수가 처리할 수 있도록 32비트 정수형 넘파이 배열로 변환합니다.
        pts = np.array(points, dtype=np.int32)
        
        # 1. Convex Hull (볼록 선체) 적용
        # 손떨림으로 인해 궤적이 안쪽으로 파이거나 지글지글한 노이즈를 제거하기 위해, 
        # 전체 점들의 가장 바깥쪽 외곽선만 고무줄로 팽팽하게 묶듯이 추출합니다.
        hull = cv.convexHull(pts)
        
        # 2. 내부 면적 검사 (꼼수 방지)
        # 그려진 궤적 내부의 픽셀 면적을 계산합니다.
        area = cv.contourArea(hull)
        # 앵커 밖에서 점만 찍고 돌아오거나, 너무 작게 그린 경우(면적 5000 미만) 실패 처리합니다.
        if area < 5000: 
            return "Fail"

        # 3. 다각형 근사화 (approxPolyDP) 및 꼭짓점 추출
        # 추출된 외곽선(hull)의 전체 둘레 길이를 구합니다. (True: 닫힌 도형임을 의미)
        perimeter = cv.arcLength(hull, True)
        
        # 오차 허용 범위(epsilon)를 둘레 길이의 5%로 설정합니다.
        # 이 값이 커지면 둥글게 그려도 각진 다각형으로 인식하고, 작아지면 매우 뾰족하게 그려야 인식합니다.
        epsilon = 0.05 * perimeter
        
        # 설정한 오차 범위를 바탕으로 도형을 단순한 다각형으로 근사화합니다.
        approx = cv.approxPolyDP(hull, epsilon, True)
        
        # 단순화된 다각형의 꼭짓점(vertices) 개수를 구합니다.
        vertices = len(approx)

        # 4. 꼭짓점 개수를 통한 최종 도형 판별
        # 꼭짓점이 3개면 삼각형, 4개면 사각형, 5개면 오각형으로 판별하여 결과를 반환합니다.
        if vertices == 3: 
            return "Triangle"
        elif vertices == 4: 
            return "Square"
        elif vertices == 5: 
            return "Pentagon"

        # 위 조건에 아무것도 해당하지 않는 알 수 없는 모양이면 실패 처리합니다.
        return "Fail"