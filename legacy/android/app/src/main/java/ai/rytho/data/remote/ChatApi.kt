package ai.rytho.data.remote

import retrofit2.http.Body
import retrofit2.http.POST

data class ChatMessageDto(
    val sender: String,
    val text: String
)

data class ChatApiRequest(
    val history: List<ChatMessageDto>,
    val message: String
)

data class ChatApiResponse(
    val status: String,
    val reply: String?
)

interface ChatApi {
    @POST("api/v1/face-reading/chat")
    suspend fun sendMessage(@Body request: ChatApiRequest): ChatApiResponse
}
