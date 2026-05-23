"""
파일명: main.py
설명: 'SplitBrain Challenge' 프로젝트의 메인 진입점(Entry Point)입니다.
웹캠으로부터 실시간으로 프레임을 읽어오고, 각 모듈(손 추적, 도형 인식, 게임 로직, UI 렌더링)을 
조립(Composition)하여 전체 게임 루프를 제어하는 컨트롤러 역할을 수행합니다.
"""

# 각 기능별로 분리된 모듈들을 불러옵니다.
import cv2
from hand_tracker import HandTracker
from shape_recognizer import ShapeRecognizer
from game_manager import GameManager
from ui_renderer import UIRenderer

def main():
    # 1. 웹캠 캡처 객체 초기화 (0번은 기본 내장 카메라를 의미합니다)
    cap = cv2.VideoCapture(0)
    
    # 웹캠의 해상도를 넓게 설정합니다 (1280x720)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # 2. 객체 지향 프로그래밍(OOP)의 '합성(Composition)' 원칙을 적용하여 객체들을 인스턴스화합니다.
    # 각 객체는 자신의 명확한 역할만 수행하며, main.py는 이들을 연결해줍니다.

    hand_tracker = HandTracker()       # MediaPipe를 이용해 손가락 좌표만 추출하는 객체
    shape_recognizer = ShapeRecognizer() # 추출된 좌표를 모아 도형으로 판별하는 객체
    game_manager = GameManager()       # 현재 라운드, 성공 횟수, 게임 클리어 여부를 관리하는 객체
    ui_renderer = UIRenderer()         # 웹캠 프레임 위에 텍스트와 그림을 덧그리는 객체


    print("시스템 초기화 완료. 게임을 시작합니다...")

    # 3. 메인 게임 루프 (실시간 영상 처리를 위한 무한 루프)
    while cap.isOpened():
        # 프레임 단위로 영상 읽기 (success: 성공 여부 bool, frame: 이미지 배열)
        success, frame = cap.read()
        if not success:
            print("웹캠을 찾을 수 없거나 프레임을 읽어올 수 없습니다.")
            break

        # 4. 거울 모드 적용 (직관적인 드로잉을 위해 화면을 좌우 반전시킵니다)
        frame = cv2.flip(frame, 1)

        # -------------------------------------------------------------
        # 아래는 앞으로 모듈들을 구현한 뒤 주석을 해제하여 작동시킬 핵심 로직입니다.
        # -------------------------------------------------------------
        
        
        # [STEP 1] 손가락 위치 추적
        # hand_tracker에게 프레임을 넘겨주면, 양손 검지손가락의 (x,y) 좌표를 반환합니다.
        left_finger, right_finger = hand_tracker.get_index_fingers(frame)

        # [STEP 2] 게임 상태 업데이트 및 도형 인식
        # 현재 화면이 '대기(START 대기)' 상태인지, '게임 진행 중'인지 확인합니다.
        current_state = game_manager.get_state()

        if current_state == "WAITING":
            # 대기 상태일 때는 START 버튼 영역에 손가락이 올라가 있는지 체크합니다.
            is_start_triggered = game_manager.check_start_button(left_finger, right_finger)
            if is_start_triggered:
                game_manager.start_game() # 게임 상태를 1라운드로 변경

        elif current_state == "PLAYING":
            # 게임 진행 중일 때는 손가락 좌표를 shape_recognizer에 넘겨 궤적을 저장하고 분석합니다.
            #left_shape, right_shape = shape_recognizer.update_and_recognize(left_finger, right_finger)
            # 인식된 도형 결과를 game_manager에 넘겨 이번 라운드의 목표와 일치하는지 평가합니다.
            # 성공 시 횟수를 증가시키고, 3번 연속 성공 시 다음 라운드로 자동으로 넘깁니다.
            #game_manager.evaluate_shapes(left_shape, right_shape)
            game_manager.process_play_state(left_finger, right_finger, shape_recognizer)
            
        elif current_state == "ROUND_CLEAR":
            game_manager.process_transition_state()

        # [STEP 3] UI 렌더링 (화면에 그리기)
        # 처리된 모든 정보(게임 상태, 손가락 위치, 현재 그려진 궤적 등)를 ui_renderer에 넘겨 화면을 그립니다.
        frame = ui_renderer.draw_all(
            frame=frame,
            state=game_manager.get_state(),
            round_info=game_manager.get_current_round_info(),
            left_finger=left_finger,
            right_finger=right_finger,
            trajectories=shape_recognizer.get_trajectories(),
            game_manager=game_manager # UI가 앵커 정보를 알게 함
        )
        

       # 5. 안내 텍스트
        cv2.putText(frame, "Press 'ESC' to Quit", (50, 650), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("SplitBrain Challenge", frame)

        # 6. 종료 아스키 코드 27번(ESC)을 감지하도록 변경
        if cv2.waitKey(1) & 0xFF == 27:
            print("사용자가 게임을 종료했습니다.")
            break

    # 7. 자원 해제 (루프 종료 후 안전하게 카메라와 창을 닫아줍니다)
    cap.release()
    cv2.destroyAllWindows()

# 이 스크립트가 직접 실행될 때만 main() 함수를 호출하도록 하는 파이썬의 표준 관례입니다.
if __name__ == "__main__":
    main()