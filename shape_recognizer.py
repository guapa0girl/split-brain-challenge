import cv2
import numpy as np

class ShapeRecognizer:
    def __init__(self):
        # 궤적 길이 제한을 없애고(또는 아주 크게) 전체 그림을 온전히 담도록 변경
        self.trajectories = {'left': [], 'right': []}

    def get_trajectories(self):
        return self.trajectories

    def clear_trajectory(self, hand):
        self.trajectories[hand] = []

    def add_point(self, hand, point):
        """손가락이 앵커(시작점) 밖으로 나가 그림을 그리는 동안 좌표를 누적합니다."""
        if point:
            self.trajectories[hand].append(point)

    def evaluate_strict_shape(self, hand, target_shape):
        """
        궤적이 시작점으로 돌아왔을 때 단 한 번 호출되어 모양을 엄격하게 판별합니다.
        """
        points = self.trajectories[hand]
        if len(points) < 15: # 너무 짧은 점들은 무시
            return "Fail"

        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        dx = max(x_coords) - min(x_coords)
        dy = max(y_coords) - min(y_coords)

        # [1라운드] 직선 꼼수 방지: 
        # 가로선은 좌우 이동거리(dx)가 길어야 하고 위아래 흔들림(dy)은 적어야 합니다.
        if target_shape == "Horizontal":
            if dx > 150 and dy < (dx * 0.5): return "Horizontal"
            return "Fail"
            
        if target_shape == "Vertical":
            if dy > 150 and dx < (dy * 0.5): return "Vertical"
            return "Fail"

        # [2, 3라운드] 다각형 꼼수 방지
        pts = np.array(points, dtype=np.int32)
        hull = cv2.convexHull(pts)
        
        # 꼼수 방지 1: 그려진 내부 면적이 너무 작으면(점만 찍으면) 실패 처리
        area = cv2.contourArea(hull)
        if area < 5000: 
            return "Fail"

        perimeter = cv2.arcLength(hull, True)
        epsilon = 0.05 * perimeter
        approx = cv2.approxPolyDP(hull, epsilon, True)
        vertices = len(approx)

        if vertices == 3: return "Triangle"
        elif vertices == 4: return "Square"
        elif vertices == 5: return "Pentagon"

        return "Fail"