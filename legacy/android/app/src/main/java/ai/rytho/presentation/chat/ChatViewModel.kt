package ai.rytho.presentation.chat

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.rytho.domain.model.ChatMessage
import ai.rytho.domain.model.MessageSender
import ai.rytho.domain.repository.ChatRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isSending: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        val initialReading = savedStateHandle.get<String>("initialReading")
        val greetingText = if (!initialReading.isNull_or_Empty()) {
            "Merhaba, kozmik yüz okumanı inceledim:\n\n\"$initialReading\"\n\nHangi konuda daha derin bir rehberlik almak istersin?"
        } else {
            "Hoş geldin ✨ Ben senin Cosmic Confidant rehberinim. Yıldız haritan, yüz okuman veya hayatındaki spiritüel soruların hakkında ne merak ediyorsun?"
        }

        val welcomeMsg = ChatMessage(
            sender = MessageSender.CONFIDANT,
            text = greetingText
        )
        _uiState.value = ChatUiState(messages = listOf(welcomeMsg))
    }

    fun sendMessage(text: String) {
        if (text.isBlank() || _uiState.value.isSending) return

        val userMessage = ChatMessage(sender = MessageSender.USER, text = text)
        val currentMessages = _uiState.value.messages + userMessage
        _uiState.value = _uiState.value.copy(messages = currentMessages, isSending = true, error = null)

        viewModelScope.launch {
            chatRepository.sendMessage(history = currentMessages.dropLast(1), userMessage = text).fold(
                onSuccess = { replyText ->
                    val aiMessage = ChatMessage(sender = MessageSender.CONFIDANT, text = replyText)
                    _uiState.value = _uiState.value.copy(
                        messages = _uiState.value.messages + aiMessage,
                        isSending = false
                    )
                },
                onFailure = { err ->
                    _uiState.value = _uiState.value.copy(
                        isSending = false,
                        error = err.message ?: "Bağlantıda bir sorun oluştu."
                    )
                }
            )
        }
    }
}

private fun String?.isNull_or_Empty(): Boolean = this == null || this.trim().isEmpty()
