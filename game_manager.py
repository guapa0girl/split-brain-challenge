"""
파일명: game_manager.py
설명: 게임의 전체적인 흐름을 제어하는 상태 머신입니다.
각 라운드의 미션과 시작점(Anchor)을 관리하고, 엄격한 도형 평가 로직을 통제합니다.
"""

class GameManager:
    def __init__(self):
        self.state = "WAITING"
        self.current_round = 1
        self.success_count = 0
        self.start_button_box = [540, 300, 740, 420]
        self.hover_frames = 0
        
        self.round_missions = {
            1: {"left": "Horizontal", "right": "Vertical"},
            2: {"left": "Triangle", "right": "Square"},
            3: {"left": "Square", "right": "Pentagon"}
        }

        # [핵심] 양손의 시작점(Anchor) 위치 정의: (Center_X, Center_Y, Radius)
        self.anchors = {
            "left": (350, 260, 40),  
            "right": (930, 260, 40) 
        }
        
        self.is_drawing = {"left": False, "right": False}
        self.completed = {"left": False, "right": False}

    def get_state(self):
        """현재 게임의 상태를 반환합니다."""
        return self.state

    def get_current_round_info(self):
        """현재 라운드 번호와 양손의 미션 정보를 반환합니다."""
        if self.current_round in self.round_missions:
            return self.current_round, self.round_missions[self.current_round]
        return self.current_round, {"left": "None", "right": "None"}

    def check_start_button(self, left_finger, right_finger):
        """프레임 드랍 및 손떨림 보완이 적용된 시작 버튼 호버링 체크"""
        fingers = [f for f in (left_finger, right_finger) if f is not None]
        is_hovering = False
        
        for finger in fingers:
            fx, fy = finger
            if (self.start_button_box[0] < fx < self.start_button_box[2] and 
                self.start_button_box[1] < fy < self.start_button_box[3]):
                is_hovering = True
                break 

        if is_hovering:
            self.hover_frames += 1
            print(f"START 버튼 인식 중... {self.hover_frames}/30") 
            if self.hover_frames >= 30:
                self.hover_frames = 0 
                return True
        else:
            if self.hover_frames > 0:
                self.hover_frames -= 2 
            else:
                self.hover_frames = 0
                
        return False

    def start_game(self):
        """게임을 시작하고 1라운드로 진입합니다."""
        self.state = "PLAYING"
        self.current_round = 1
        self.success_count = 0
        self._reset_turn()
        print("게임을 시작합니다! 1라운드 진입.")
        
    def _reset_turn(self):
        """드로잉 상태 및 성공 여부를 초기화합니다."""
        self.is_drawing = {"left": False, "right": False}
        self.completed = {"left": False, "right": False}

    def process_play_state(self, left_finger, right_finger, shape_recognizer):
        """main.py에서 매 프레임 호출되어 양손의 앵커 출입 상태와 드로잉을 제어합니다."""
        target = self.round_missions[self.current_round]

        self._process_hand("left", left_finger, target["left"], shape_recognizer)
        self._process_hand("right", right_finger, target["right"], shape_recognizer)

        if self.completed["left"] and self.completed["right"]:
            self.success_count += 1
            print(f"🎉 동시 성공! 연속 성공: {self.success_count}/3")
            self._reset_turn()
            shape_recognizer.clear_trajectory("left")
            shape_recognizer.clear_trajectory("right")
            
            if self.success_count >= 3:
                self._advance_round()

    def _process_hand(self, hand, finger, target_shape, shape_recognizer):
        if not finger: return 
        if self.completed[hand]: return 

        ax, ay, ar = self.anchors[hand]
        fx, fy = finger
        
        distance = ((fx - ax)**2 + (fy - ay)**2)**0.5
        in_anchor = distance < ar

        if in_anchor:
            if self.is_drawing[hand]:
                # 1. 밖에서 그림을 그리다가 앵커 안으로 돌아왔을 때 (도착)
                self.is_drawing[hand] = False
                shape_recognizer.add_point(hand, finger) # 도착한 점도 궤적에 포함
                
                result = shape_recognizer.evaluate_strict_shape(hand, target_shape)
                
                if result == target_shape:
                    self.completed[hand] = True 
                    print(f"[{hand}] {target_shape} 정확히 그리기 성공!")
                else:
                    print(f"[{hand}] 실패! 다시 그리세요. (인식결과: {result})")
                    
                # 2. 채점 후에는 궤적을 비워서 화면의 선을 지워줍니다.
                shape_recognizer.clear_trajectory(hand) 
            else:
                # 3. 앵커 안에서 출발 대기 중일 때 (수정된 부분)
                # 앵커 안에서도 선이 예쁘게 시작되도록 좌표를 계속 누적합니다.
                shape_recognizer.add_point(hand, finger)
                
                # 단, 앵커 안에 가만히 있을 때 무한정 점이 쌓여 오작동하는 것을 방지하기 위해 
                # 가장 최근의 점 30개(약 1초 분량)만 남기고 예전 점은 지워줍니다.
                if len(shape_recognizer.trajectories[hand]) > 30:
                    shape_recognizer.trajectories[hand].pop(0)
        else:
            # 4. 앵커 밖으로 나갔을 때 (그리기 시작)
            if not self.is_drawing[hand]:
                self.is_drawing[hand] = True
            shape_recognizer.add_point(hand, finger)

    def _advance_round(self):
        self.current_round += 1
        self.success_count = 0
        if self.current_round > 3:
            self.state = "CLEARED"
            print("축하합니다! 모든 라운드를 클리어했습니다.")
        else:
            print(f"다음 라운드로 진입합니다: {self.current_round}라운드")