'''
(From LiveKit Docs)
Sample video frames 
LLMs can process video in the form of still images, but many LLMs are not trained for this use case and can produce suboptimal results in understanding motion and other changes through a video feed. Realtime models, like Gemini Live, are trained on video and you can enable live video input for automatic support.
If you are using an STT-LLM-TTS pipeline, you can still work with video by sampling the video track at suitable times. For instance, in the following example the agent always includes the latest video frame on each conversation turn from the user. This provides the model with additional context without overwhelming it with data or expecting it to interpret many sequential frames at a time:

'''
import asyncio
from livekit import rtc
from livekit.agents import Agent, get_job_context
from livekit.agents.llm import ImageContent

class Assistant(Agent):
    def __init__(self) -> None:
        self._latest_frame = None
        self._video_stream = None
        self._tasks = []
        super().__init__(instructions="You are a helpful voice AI assistant.")
    
    async def on_enter(self):
        room = get_job_context().room

        # Find the first video track (if any) from the remote participant
        remote_participant = list(room.remote_participants.values())[0]
        video_tracks = [publication.track for publication in list(remote_participant.track_publications.values()) if publication.track.kind == rtc.TrackKind.KIND_VIDEO]
        if video_tracks:
            self._create_video_stream(video_tracks[0])
        
        # Watch for new video tracks not yet published
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)
                        
    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        # Add the latest video frame, if any, to the new message
        if self._latest_frame:
            new_message.content.append(ImageContent(image=self._latest_frame))
            self._latest_frame = None
    
    # Helper method to buffer the latest video frame from the user's track
    def _create_video_stream(self, track: rtc.Track):
        # Close any existing stream (we only want one at a time)
        if self._video_stream is not None:
            self._video_stream.close()

        # Create a new stream to receive frames    
        self._video_stream = rtc.VideoStream(track)
        async def read_stream():
            async for event in self._video_stream:
                # Store the latest frame for use later
                self._latest_frame = event.frame
        
        # Store the async task
        task = asyncio.create_task(read_stream())
        task.add_done_callback(lambda t: self._tasks.remove(t))
        self._tasks.append(task)