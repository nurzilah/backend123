from flask import Blueprint, jsonify, request

video_api = Blueprint('video_api', __name__)

video_therapy_data = {
    1: [
        {"videoId": "chzl_w2AwxI", "title": "Cheeks Exercises", "description": "Cheek and lip muscle exercises to improve coordination and strength for Bell's palsy recovery.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "lFRoiq6_X-o", "title": "Mouth Exercise", "description": "Mouth and lip exercises designed to strengthen facial muscles.", "duration": "2 min", "repetition": "8x"},
        {"videoId": "Deqbv16u--U", "title": "Eye Exercise", "description": "Eye closure exercises to enhance eyelid muscle strength.", "duration": "1.5 min", "repetition": "12x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Facial massage for relieving muscle tension and improving circulation.", "duration": "3 min", "repetition": "5x"}
    ],
    2: [
        {"videoId": "abR1NSb_cTI", "title": "Cheeks Exercises", "description": "Cheek and lip muscle routine for restoring facial muscle balance.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "bJA8s_41ip0", "title": "Mouth Exercise", "description": "Lip strengthening exercise to regain control.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "ZDvFxesPNIE", "title": "Eye Exercise", "description": "Blinking and eye closure exercises for strengthening eye muscles.", "duration": "1.5 min", "repetition": "10x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Gentle massage to stimulate facial nerve activity.", "duration": "3 min", "repetition": "6x"}
    ],
    3: [
        {"videoId": "f07NDq6L_5M", "title": "Eye Exercise", "description": "Eye movement and closure drills to improve muscle responsiveness.", "duration": "1.5 min", "repetition": "12x"},
        {"videoId": "1LDmHrCrq2k", "title": "Mouth Exercise", "description": "Smile, frown, and pout exercises for better muscle control.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "UaQ5kSL44GM", "title": "Cheek Exercise", "description": "Puff and hold exercises to target cheek muscles.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Circular massage motion to ease tension and improve flow.", "duration": "3 min", "repetition": "5x"}
    ],
    4: [
        {"videoId": "8X_n7N-Ipxw", "title": "Eye Exercise", "description": "Focus and close eyes to improve control and range.", "duration": "1.5 min", "repetition": "12x"},
        {"videoId": "58C2cmmj018", "title": "Mouth Exercise", "description": "Tongue and lip exercises for coordination and strength.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "abR1NSb_cTI", "title": "Cheek Exercise", "description": "Cheek puffing, smile holding drills to tone muscles.", "duration": "2 min", "repetition": "8x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Relaxing full-face massage for nerve recovery.", "duration": "3 min", "repetition": "6x"}
    ],
    5: [
        {"videoId": "12Up8-dCRLM", "title": "Eye Exercise", "description": "Squeeze-shut and relax eye routines to increase control.", "duration": "1.5 min", "repetition": "10x"},
        {"videoId": "air_AhKfXQE", "title": "Mouth Exercise", "description": "Mouth opening and stretching movements.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "chzl_w2AwxI", "title": "Cheek Exercise", "description": "Puff cheeks and hold to strengthen the muscles.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Soothing massage to release facial tension.", "duration": "3 min", "repetition": "5x"}
    ],
    6: [
        {"videoId": "12Up8-dCRLM", "title": "Eye Exercise", "description": "Upper eyelid mobility exercises.", "duration": "1.5 min", "repetition": "10x"},
        {"videoId": "x4n_wiAj8vw", "title": "Mouth Exercise", "description": "Lip stretching and holding movements.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "UaQ5kSL44GM", "title": "Cheek Exercise", "description": "Strengthening routines for cheek control.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Massage techniques for daily nerve stimulation.", "duration": "3 min", "repetition": "5x"}
    ],
    7: [
        {"videoId": "f07NDq6L_5M", "title": "Eye Exercise", "description": "Eye tracking and full closure practice.", "duration": "1.5 min", "repetition": "12x"},
        {"videoId": "46-R-BXBEl8", "title": "Mouth Exercise", "description": "Advanced lip movement drills for symmetry.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "abR1NSb_cTI", "title": "Cheek Exercise", "description": "Final cheek movement sets to complete the week.", "duration": "2 min", "repetition": "10x"},
        {"videoId": "kuI7mkWPMq4", "title": "Face Massage", "description": "Final relaxing massage for full therapy week.", "duration": "3 min", "repetition": "6x"}
    ]
}


@video_api.route('/videos', methods=['GET'])
def get_videos():
    day = request.args.get('day', type=int)
    if day is None or day not in video_therapy_data:
        return jsonify({'error': 'Invalid or missing day parameter'}), 400
    return jsonify({'day': day, 'videos': video_therapy_data[day]})

@video_api.route('/therapy/day/<int:day>', methods=['GET'])
def get_videos_by_day(day):
    if day not in video_therapy_data:
        return jsonify({'error': 'Invalid day'}), 400
    return jsonify(video_therapy_data[day])

