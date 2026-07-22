package ai.rytho.data.repository

import ai.rytho.data.remote.ChatApi
import ai.rytho.data.remote.ChatApiRequest
import ai.rytho.data.remote.ChatMessageDto
import ai.rytho.domain.model.ChatMessage
import ai.rytho.domain.repository.ChatRepository
import javax.inject.Inject

class ChatRepositoryImpl @Inject constructor(
    private val chatApi: ChatApi
) : ChatRepository {

    override suspend fun sendMessage(history: List<ChatMessage>, userMessage: String): Result<String> {
        return try {
            val historyDtos = history.map {
                ChatMessageDto(
                    sender = it.sender.name,
                    text = it.text
                )
            }
            val response = chatApi.sendMessage(
                ChatApiRequest(history = historyDtos, message = userMessage)
            )
            if (response.status == "success" && response.reply != null) {
                Result.success(response.reply)
            } else {
                Result.failure(Exception("Cosmic Confidant yanıt vermekte zorlandı."))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
