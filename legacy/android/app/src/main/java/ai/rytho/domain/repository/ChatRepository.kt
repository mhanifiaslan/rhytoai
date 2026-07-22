package ai.rytho.domain.repository

import ai.rytho.domain.model.ChatMessage

interface ChatRepository {
    suspend fun sendMessage(history: List<ChatMessage>, userMessage: String): Result<String>
}
