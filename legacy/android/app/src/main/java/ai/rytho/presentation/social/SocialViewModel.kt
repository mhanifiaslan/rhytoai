package ai.rytho.presentation.social

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.rytho.domain.model.SocialPost
import ai.rytho.domain.repository.AuthRepository
import ai.rytho.domain.repository.SocialRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SocialViewModel @Inject constructor(
    private val socialRepository: SocialRepository,
    private val authRepository: AuthRepository
) : ViewModel() {

    val posts: StateFlow<List<SocialPost>> = socialRepository.getSocialPosts()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    fun createPost(content: String) {
        val user = authRepository.getCurrentUser()
        val name = user?.displayName ?: user?.email ?: "Kozmik Gezgin"
        viewModelScope.launch {
            socialRepository.createPost(
                content = content,
                authorName = name,
                zodiac = "Scorpio ♏"
            )
        }
    }
}
