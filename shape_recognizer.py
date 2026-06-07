"""
파일명: shape_recognizer.py
설명: 사용자의 손가락 궤적 좌표를 누적하고, 수학적 분석을 통해 어떤 도형인지 판별하는 두뇌 모듈
단순히 좌표를 잇는 것에 그치지 않고, 손떨림 노이즈 제거(Convex Hull) 및 꼼수 방지 알고리즘 사용
"""

import cv2 as cv
import numpy as np

class ShapeRecognizer:
    def __init__(self):
        # 전체 그림을 온전히 담기 위해 양손 궤적 리스트를 별도로 초기화
        self.trajectories = {'left': [], 'right': []}

    def get_trajectories(self):
        return self.trajectories

    def clear_trajectory(self, hand):
        # 특정 손의 궤적 데이터를 비워 화면에서 선을 완전히 지우기
        self.trajectories[hand] = []

    def add_point(self, hand, point):
        # 그리는 중 매 프레임마다 인식된 손가락의 픽셀 좌표 누적
        if point: 
            self.trajectories[hand].append(point)

    def evaluate_strict_shape(self, hand, target_shape):
        # 궤적이 앵커로 돌아왔을 때 한 번 호출되어 도형을 채점
        points = self.trajectories[hand]
        
        # 오작동 방지: 누적된 좌표(점)가 20개 미만이면 무시
        if len(points) < 20: 
            return "Fail"

        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        dx = max(x_coords) - min(x_coords)
        dy = max(y_coords) - min(y_coords)

        # [1라운드: 직선 미션] 좌우 흔들림(dy) 및 상하 흔들림(dx) 비율을 계산해 꼼수 선 긋기 차단
        if target_shape == "Horizontal": 
            return "Horizontal" if dx > 150 and dy < (dx * 0.5) else "Fail"
            
        if target_shape == "Vertical": 
            return "Vertical" if dy > 150 and dx < (dy * 0.5) else "Fail"

        # [2,3라운드: 다각형 미션] OpenCV 호환성을 위해 32비트 정수형 넘파이 배열로 변환
        pts = np.array(points, dtype=np.int32)
        
        # Convex Hull 알고리즘을 사용해 손떨림 등 안쪽으로 파고든 궤적(노이즈)을 팽팽하게 펴주기
        hull = cv.convexHull(pts)
        
        # 내부 면적 계산: 앵커 밖에서 점만 찍거나 너무 작게 그린 꼼수를 잡아내기
        if cv.contourArea(hull) < 5000: 
            return "Fail"

        # approxPolyDP를 사용해 도형의 둘레 길이 대비 오차 범위를 허용하여 다각형으로 근사화
        perimeter = cv.arcLength(hull, True)
        
        # 삼각형은 오차 범위를 넓혀(0.05) 더 잘 인식되게 하고, 나머지는 기본(0.03) 적용
        epsilon_val = 0.05 if target_shape == "Triangle" else 0.03
        approx = cv.approxPolyDP(hull, epsilon_val * perimeter, True)
        vertices = len(approx)

        # 최종 꼭짓점 개수로 도형을 확정
        if target_shape == "Triangle":
            return "Triangle" if vertices == 3 else "Fail"
            
        elif target_shape == "Square":
            # 사각형은 꼭짓점 4개 확인 + 가로세로 비율(aspect ratio) 0.7~1.3 체크로 깐깐하게 변경
            if vertices == 4:
                x, y, w, h = cv.boundingRect(approx)
                aspect_ratio = float(w) / h
                return "Square" if 0.7 <= aspect_ratio <= 1.3 else "Fail"
            return "Fail"
            
        elif target_shape == "Pentagon":
            return "Pentagon" if vertices == 5 else "Fail"

        return "Fail"