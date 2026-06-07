"""
파일명: game_manager.py
설명: 게임의 전체적인 흐름(상태)과 점수를 제어하는 상태 머신
양손이 완전히 독립적으로 미션을 수행하며, 라운드 클리어 시 전환 효과 및 최종 클리어 관리, 시간 계산
"""

import time # 타이머

class GameManager:
    def __init__(self):
        self.state = "WAITING"
        self.current_round = 1
        
        # 양손의 성공 횟수를 개별적으로 관리하여 완전한 독립형 멀티태스킹 구현
        self.success_count = {"left": 0, "right": 0}
        
        # 사용자가 그린 삐뚤빼뚤한 궤적 좌표를 그대로 보관
        self.success_shapes = {"left": [], "right": []}
        
        # 라운드 전환 효과를 띄워줄 시간을 계산하는 프레임 카운터
        self.transition_frames = 0
        
        # START 버튼의 좌표 영역 [x1, y1, x2, y2]
        self.start_button_box = [540, 300, 740, 420]
        self.hover_frames = 0
        
        # RESTART 버튼 좌측 하단, QUIT 버튼 우측 하단으로 좌표 변경
        self.restart_button_box = [30, 620, 230, 680] 
        self.restart_hover_frames = 0
        
        # 종료(QUIT) 버튼 좌표 영역 설정
        self.quit_button_box = [1050, 620, 1250, 680]
        self.quit_hover_frames = 0
        
        # 타이머 및 RESTART 기능 관련 변수
        self.start_time = None
        self.end_time = None
        self.best_time = float('inf') # 최단 시간 (무한대로 초기화)
        
        # 각 라운드별 양손에 주어지는 미션 목표
        self.round_missions = {
            1: {"left": "Horizontal", "right": "Vertical"},
            2: {"left": "Triangle", "right": "Square"},
            3: {"left": "Square", "right": "Pentagon"}
        }

        # 양손이 그림을 시작하고 끝내는 '시작점(Anchor)' 좌표 (x, y, 반지름)
        self.anchors = {
            "left": (350, 260, 40),  
            "right": (930, 260, 40) 
        }
        
        # 현재 화면 밖에서 선을 그리고 있는지 여부를 판별하는 플래그
        self.is_drawing = {"left": False, "right": False}

    def get_state(self):
        return self.state

    def get_current_round_info(self):
        if self.current_round in self.round_missions:
            return self.current_round, self.round_missions[self.current_round]
        return self.current_round, {"left": "None", "right": "None"}

    def check_start_button(self, left_finger, right_finger):
        # 두 손가락이 모두 각각의 START 앵커 원 안에 있는지 확인
        if left_finger is None or right_finger is None:
            self.hover_frames = max(0, self.hover_frames - 2)
            return False
            
        lax, lay, lar = self.anchors["left"]
        rax, ray, rar = self.anchors["right"]
        
        # 유클리드 거리로 양손이 모두 각자의 앵커 영역 안에 들어왔는지 계산
        left_in = ((left_finger[0] - lax)**2 + (left_finger[1] - lay)**2)**0.5 < lar
        right_in = ((right_finger[0] - rax)**2 + (right_finger[1] - ray)**2)**0.5 < rar

        # 두 손가락 모두 앵커 안에 있을 때만 게이지 증가
        if left_in and right_in:
            self.hover_frames += 1
            if self.hover_frames >= 30: # 약 1초(30프레임) 유지 시 게임 시작
                self.hover_frames = 0 
                return True
        else:
            self.hover_frames = max(0, self.hover_frames - 2) # 하나라도 떼면 게이지 감소
            
        return False

    def start_game(self):
        self.state = "PLAYING"
        self.current_round = 1
        self.success_count = {"left": 0, "right": 0}
        self.success_shapes = {"left": [], "right": []} # [수정됨] 시작 시 궤적 데이터 초기화
        self.is_drawing = {"left": False, "right": False}
        self.start_time = time.time() # 게임 시작과 동시에 타이머 시작

    def process_play_state(self, left_finger, right_finger, shape_recognizer):
        # 양손의 궤적을 평가하고 라운드 클리어 여부 검사
        target = self.round_missions[self.current_round]

        self._process_hand("left", left_finger, target["left"], shape_recognizer)
        self._process_hand("right", right_finger, target["right"], shape_recognizer)

        # 양손 모두 3번 이상 성공했다면 다음 라운드로 넘어갈 준비
        if self.success_count["left"] >= 3 and self.success_count["right"] >= 3:
            shape_recognizer.clear_trajectory("left")
            shape_recognizer.clear_trajectory("right")
            
            # 3라운드일 경우 전환 화면을 생략하고 곧바로 최종 클리어로 직행!
            if self.current_round >= 3:
                self.state = "CLEARED"
                
                # 3라운드 클리어 시 타이머를 종료하고 최고 기록 갱신
                self.end_time = time.time() 
                elapsed = self.end_time - self.start_time
                if elapsed < self.best_time:
                    self.best_time = elapsed
                print(f"CONGRATULATIONS! 모든 라운드를 통과하였습니다. (기록: {elapsed:.1f}초)")
                
            else:
                # 1, 2라운드일 경우 전환 효과 상태(ROUND_CLEAR)로 돌입
                self.state = "ROUND_CLEAR"
                self.transition_frames = 0 

    def process_transition_state(self):
        # 라운드 클리어 이펙트를 일정 시간 띄워준 뒤 다음 라운드 진행
        self.transition_frames += 1
        if self.transition_frames > 30: # 약 1초 대기
            self._advance_round()

    def _process_hand(self, hand, finger, target_shape, shape_recognizer):
        # 각 손의 위치를 계산하여 궤적을 그리고 채점
        if not finger: return 

        ax, ay, ar = self.anchors[hand]
        fx, fy = finger
        
        # 손가락과 시작점(Anchor) 사이의 거리를 유클리드 거리 공식으로 계산
        in_anchor = ((fx - ax)**2 + (fy - ay)**2)**0.5 < ar

        if in_anchor:
            # 1. 밖에서 그림을 다 그리고 시작점으로 돌아왔을 때 (채점 진행)
            if self.is_drawing[hand]:
                self.is_drawing[hand] = False
                shape_recognizer.add_point(hand, finger) 
                
                result = shape_recognizer.evaluate_strict_shape(hand, target_shape)
                if result == target_shape:
                    self.success_count[hand] += 1 # 정답일 경우 해당 손의 점수만 +1
                    #  성공하는 순간 삐뚤빼뚤한 실제 궤적 좌표를 저장(박제)
                    self.success_shapes[hand].append(list(shape_recognizer.trajectories[hand]))
                
                # 채점 후에는 궤적을 지우기
                shape_recognizer.clear_trajectory(hand) 
            else:
                # 2. 시작점 안에서 대기 중일 때 (시작점이 꼬리처럼 예쁘게 이어지도록 좌표 누적)
                shape_recognizer.add_point(hand, finger)
                if len(shape_recognizer.trajectories[hand]) > 30:
                    shape_recognizer.trajectories[hand].pop(0)
        else:
            # 3. 앵커 밖으로 나가서 본격적으로 그림을 그릴 때
            if not self.is_drawing[hand]:
                self.is_drawing[hand] = True
            shape_recognizer.add_point(hand, finger)

    def _advance_round(self):
        # process_transition_state 종료, 변수들을 초기화 후 다음 라운드를 시작
        self.current_round += 1
        self.success_count = {"left": 0, "right": 0}
        self.success_shapes = {"left": [], "right": []} # [추가됨] 라운드 교체 시 궤적 초기화
        self.is_drawing = {"left": False, "right": False}
        
        # 3라운드 종료는 이미 process_play_state에서 직행 처리하므로 무조건 PLAYING으로 복귀
        self.state = "PLAYING"

    # 타이머 및 RESTART 관련 메서드
    def reset_game(self, shape_recognizer):
        # HOME 기능
        self.state = "WAITING"
        self.current_round = 1
        self.success_count = {"left": 0, "right": 0}
        self.success_shapes = {"left": [], "right": []} 
        self.is_drawing = {"left": False, "right": False}
        self.transition_frames = 0
        self.hover_frames = 0 # START 버튼 게이지 초기화
        shape_recognizer.clear_trajectory("left")
        shape_recognizer.clear_trajectory("right")
        self.start_time = None # 타이머 초기화 (시작 전이므로 None)
        self.end_time = None
        print("🏠 HOME! 처음 대기 화면으로 돌아갑니다.")

    def check_restart_button(self, left_finger, right_finger, shape_recognizer):
        # 좌측 하단의 RESTART 버튼 영역 손가락 체크
        fingers = [f for f in (left_finger, right_finger) if f is not None]
        is_hovering = False
        
        for fx, fy in fingers:
            if (self.restart_button_box[0] < fx < self.restart_button_box[2] and 
                self.restart_button_box[1] < fy < self.restart_button_box[3]):
                is_hovering = True
                break 

        if is_hovering:
            self.restart_hover_frames += 1
            if self.restart_hover_frames >= 30: # 약 1초(30프레임) 유지 시 리셋
                self.restart_hover_frames = 0
                self.reset_game(shape_recognizer)
                return True
        else:
            self.restart_hover_frames = max(0, self.restart_hover_frames - 2)
        return False

    # 우측 하단의 QUIT 버튼 영역 손가락 체크
    def check_quit_button(self, left_finger, right_finger):
        fingers = [f for f in (left_finger, right_finger) if f is not None]
        is_hovering = False
        
        for fx, fy in fingers:
            if (self.quit_button_box[0] < fx < self.quit_button_box[2] and 
                self.quit_button_box[1] < fy < self.quit_button_box[3]):
                is_hovering = True
                break 

        if is_hovering:
            self.quit_hover_frames += 1
            if self.quit_hover_frames >= 30: # 약 1초(30프레임) 유지 시 종료
                self.quit_hover_frames = 0
                return True
        else:
            self.quit_hover_frames = max(0, self.quit_hover_frames - 2)
        return False

    def get_time_info(self):
        # 화면에 띄워줄 현재 경과 시간과 최고 기록 반환
        if self.start_time is None:
            return 0.0, self.best_time
            
        if self.state == "CLEARED" and self.end_time is not None:
            cur_time = self.end_time - self.start_time
        else:
            cur_time = time.time() - self.start_time
            
        return cur_time, self.best_time