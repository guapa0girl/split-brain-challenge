"""
파일명: main.py
설명: 'SplitBrain Challenge' 프로젝트의 메인 진입점(Entry Point)
웹캠으로부터 실시간으로 프레임을 읽어오고, 각 모듈(손 추적, 도형 인식, 게임 로직, UI 렌더링)을 
조립(Composition)하여 전체 게임 루프를 제어하는 컨트롤러 역할
"""

import cv2 as cv
from hand_tracker import HandTracker
from shape_recognizer import ShapeRecognizer
from game_manager import GameManager
from ui_renderer import UIRenderer

def main():
    # 1. 웹캠 캡처 객체 초기화
    cap = cv.VideoCapture(0)
    
    # 웹캠의 해상도를 넓게 설정합니다 (1280x720)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720)

    # 2. 객체 지향 프로그래밍(OOP)의 '합성(Composition)' 원칙 적용
    # 각 객체는 자신의 명확한 역할만 수행하며, main.py는 이들을 연결해주는 뼈대
    hand_tracker = HandTracker()         # MediaPipe를 이용해 손가락 좌표만 추출
    shape_recognizer = ShapeRecognizer() # 추출된 좌표를 모아 도형으로 판별
    game_manager = GameManager()         # 라운드, 성공 횟수, 게임 클리어 여부 등 상태 관리
    ui_renderer = UIRenderer()           # 웹캠 프레임 위에 텍스트와 가이드 선 그리기

    print("시스템 초기화 완료. 게임을 시작합니다...")

    # 3. 메인 게임 루프 (실시간 영상 처리를 위한 무한 루프)
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("웹캠을 찾을 수 없거나 프레임을 읽어올 수 없습니다.")
            break

        # 4. 거울 모드 적용 (직관적인 드로잉을 위해 화면을 좌우 반전)
        frame = cv.flip(frame, 1)

        # [STEP 1] 손가락 위치 추적
        # hand_tracker에게 프레임을 넘겨 양손 검지손가락의 (x,y) 좌표 받기
        left_finger, right_finger = hand_tracker.get_index_fingers(frame)

        # [STEP 2] 게임 상태 업데이트 및 로직 처리
        current_state = game_manager.get_state()

        # 대기 상태(WAITING)와 그 외 상태(게임 진행/클리어 등)를 분리하여 버튼을 항시 감지하도록 변경
        if current_state == "WAITING":
            # 대기 상태: START 버튼 영역에 손가락이 1초 이상 머무는지 체크
            is_start_triggered = game_manager.check_start_button(left_finger, right_finger)
            if is_start_triggered:
                game_manager.start_game() 
        else:
            # 게임이 시작된 이후에는 상태에 상관없이 RESTART 버튼을 항시 감지
            game_manager.check_restart_button(left_finger, right_finger, shape_recognizer)
            
            # 우측 하단의 QUIT(종료) 버튼 감지 시 안전하게 루프를 탈출하여 게임 종료
            if game_manager.check_quit_button(left_finger, right_finger):
                print("사용자가 화면의 QUIT 버튼을 눌러 게임을 종료합니다.")
                break
            
            # RESTART 버튼 등으로 인해 상태가 바뀌었을 수 있으므로 최신 상태를 다시 부르기
            current_state = game_manager.get_state()

            if current_state == "PLAYING":
                # 게임 진행 중: 손가락 좌표를 분석하고, 3회 성공 시 다음 라운드로 넘기기
                game_manager.process_play_state(left_finger, right_finger, shape_recognizer)
                
            elif current_state == "ROUND_CLEAR":
                # 라운드 전환 중: 축하 메시지를 약 2.5초(75프레임)간 띄운 후 다음 라운드로 이동
                game_manager.process_transition_state()

        # [STEP 3] UI 렌더링 (화면에 그리기)
        # 처리된 모든 정보(게임 상태, 궤적 등)를 넘겨 화면에 그래픽 요소들을 덧그리기
        frame = ui_renderer.draw_all(
            frame=frame,
            state=game_manager.get_state(),
            round_info=game_manager.get_current_round_info(),
            left_finger=left_finger,
            right_finger=right_finger,
            trajectories=shape_recognizer.get_trajectories(),
            game_manager=game_manager 
        )
        
        # 5. 종료 안내 텍스트 (화면 하단 정중앙에 배치)
        esc_text = "Press 'ESC' to Quit"
        esc_size = cv.getTextSize(esc_text, cv.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        esc_x = (1280 - esc_size[0]) // 2
        cv.putText(frame, esc_text, (esc_x, 680), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv.imshow("SplitBrain Challenge", frame)

        # 6. 아스키 코드 27번(ESC) 입력 감지 시 게임 안전 종료
        if cv.waitKey(1) & 0xFF == 27:
            print("사용자가 게임을 종료했습니다.")
            break

    # 7. 자원 해제 (루프 종료 후 안전하게 카메라와 창을 닫기)
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()