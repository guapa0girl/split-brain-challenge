"""
파일명: game_manager.py
설명: 게임의 전체적인 흐름을 제어하는 상태 머신으로
양손이 완전히 독립적으로 미션을 수행하며, 라운드 클리어 시 전환 효과를 관리합니다.
"""

class GameManager:
    def __init__(self):
        self.state = "WAITING"
        self.current_round = 1
        
        # 양손의 성공 횟수를 독립적으로 관리합니다.
        self.success_count = {"left": 0, "right": 0}
        
        # 라운드 전환 효과를 보여줄 프레임 카운터
        self.transition_frames = 0
        
        self.start_button_box = [540, 300, 740, 420]
        self.hover_frames = 0
        
        self.round_missions = {
            1: {"left": "Horizontal", "right": "Vertical"},
            2: {"left": "Triangle", "right": "Square"},
            3: {"left": "Square", "right": "Pentagon"}
        }

        self.anchors = {
            "left": (350, 260, 40),  
            "right": (930, 260, 40) 
        }
        
        self.is_drawing = {"left": False, "right": False}

    def get_state(self):
        return self.state

    def get_current_round_info(self):
        if self.current_round in self.round_missions:
            return self.current_round, self.round_missions[self.current_round]
        return self.current_round, {"left": "None", "right": "None"}

    def check_start_button(self, left_finger, right_finger):
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
        self.state = "PLAYING"
        self.current_round = 1
        self.success_count = {"left": 0, "right": 0}
        self.is_drawing = {"left": False, "right": False}
        print("게임을 시작합니다! 1라운드 진입.")

    def process_play_state(self, left_finger, right_finger, shape_recognizer):
        target = self.round_missions[self.current_round]

        self._process_hand("left", left_finger, target["left"], shape_recognizer)
        self._process_hand("right", right_finger, target["right"], shape_recognizer)

        # 양손 모두 3번 이상 성공했을 때
        if self.success_count["left"] >= 3 and self.success_count["right"] >= 3:
            shape_recognizer.clear_trajectory("left")
            shape_recognizer.clear_trajectory("right")
            
            # 현재 3라운드라면 전환 효과 없이 바로 최종 클리어 상태로 직행합니다.
            if self.current_round >= 3:
                self.state = "CLEARED"
                print("축하합니다! 모든 라운드를 클리어했습니다.")
            else:
                # 1, 2라운드일 경우 기존처럼 다음 라운드 안내 전환 효과를 띄웁니다.
                self.state = "ROUND_CLEAR"
                self.transition_frames = 0 
                print(f"🎉 {self.current_round}라운드 클리어!")

    def process_transition_state(self):
        # 라운드 클리어 이펙트를 일정 시간 띄워준 뒤 다음 라운드로 넘깁니다.
        self.transition_frames += 1
        # 약 2.5초(75프레임) 대기 후 다음 라운드로 이동
        if self.transition_frames > 75:
            self._advance_round()

    def _process_hand(self, hand, finger, target_shape, shape_recognizer):
        if not finger: return 

        ax, ay, ar = self.anchors[hand]
        fx, fy = finger
        distance = ((fx - ax)**2 + (fy - ay)**2)**0.5
        in_anchor = distance < ar

        if in_anchor:
            if self.is_drawing[hand]:
                self.is_drawing[hand] = False
                shape_recognizer.add_point(hand, finger) 
                
                result = shape_recognizer.evaluate_strict_shape(hand, target_shape)
                
                if result == target_shape:
                    self.success_count[hand] += 1 # [변경됨] 각각 독립적으로 성공 횟수 1 증가
                    print(f"[{hand}] {target_shape} 성공! ({self.success_count[hand]}/3)")
                else:
                    print(f"[{hand}] 실패! (인식결과: {result})")
                    
                shape_recognizer.clear_trajectory(hand) 
            else:
                shape_recognizer.add_point(hand, finger)
                if len(shape_recognizer.trajectories[hand]) > 30:
                    shape_recognizer.trajectories[hand].pop(0)
        else:
            if not self.is_drawing[hand]:
                self.is_drawing[hand] = True
            shape_recognizer.add_point(hand, finger)

    def _advance_round(self):
        self.current_round += 1
        self.success_count = {"left": 0, "right": 0}
        self.is_drawing = {"left": False, "right": False}
        
        if self.current_round > 3:
            self.state = "CLEARED"
            print("축하합니다! 모든 라운드를 클리어했습니다.")
        else:
            self.state = "PLAYING" # 다시 플레이 상태로 복귀
            print(f"다음 라운드로 진입합니다: {self.current_round}라운드")