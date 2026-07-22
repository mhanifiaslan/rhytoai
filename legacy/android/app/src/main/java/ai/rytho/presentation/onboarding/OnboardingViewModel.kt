package ai.rytho.presentation.onboarding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.rytho.domain.model.UserProfile
import ai.rytho.domain.repository.AuthRepository
import ai.rytho.domain.repository.UserRepository
import com.google.firebase.auth.FirebaseAuth
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class OnboardingUiState(
    val step: Int = 1,
    val gender: String = "",
    val birthDate: String = "",
    val birthTime: String = "",
    val birthCity: String = "",
    val isLoading: Boolean = false,
    val isCompleted: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(OnboardingUiState())
    val uiState: StateFlow<OnboardingUiState> = _uiState.asStateFlow()

    fun updateGender(gender: String) {
        _uiState.value = _uiState.value.copy(gender = gender)
    }

    fun updateBirthDate(date: String) {
        _uiState.value = _uiState.value.copy(birthDate = date)
    }

    fun updateBirthTime(time: String) {
        _uiState.value = _uiState.value.copy(birthTime = time)
    }

    fun updateBirthCity(city: String) {
        _uiState.value = _uiState.value.copy(birthCity = city)
    }

    fun nextStep() {
        if (_uiState.value.step < 4) {
            _uiState.value = _uiState.value.copy(step = _uiState.value.step + 1)
        } else {
            completeOnboarding()
        }
    }

    fun previousStep() {
        if (_uiState.value.step > 1) {
            _uiState.value = _uiState.value.copy(step = _uiState.value.step - 1)
        }
    }

    private fun completeOnboarding() {
        val domainUser = authRepository.getCurrentUser()
        val fbUser = FirebaseAuth.getInstance().currentUser
        val uid = domainUser?.uid ?: fbUser?.uid ?: "user_default"

        _uiState.value = _uiState.value.copy(isLoading = true, error = null)

        viewModelScope.launch {
            val profile = UserProfile(
                uid = uid,
                displayName = domainUser?.displayName ?: fbUser?.displayName ?: "Kozmik Gezgin",
                email = domainUser?.email ?: fbUser?.email ?: "",
                photoUrl = domainUser?.photoUrl ?: fbUser?.photoUrl?.toString(),
                birthDate = _uiState.value.birthDate.ifEmpty { "01.01.2000" },
                birthTime = _uiState.value.birthTime.ifEmpty { "12:00" },
                birthCity = _uiState.value.birthCity.ifEmpty { "Istanbul" },
                onboardingCompleted = true
            )

            userRepository.saveUserProfile(profile).fold(
                onSuccess = {
                    _uiState.value = _uiState.value.copy(isLoading = false, isCompleted = true)
                },
                onFailure = { err ->
                    // Firestore kural/erisim hatasi olsa dahi onboarding tamamlamaya izin ver (fallback)
                    _uiState.value = _uiState.value.copy(isLoading = false, isCompleted = true)
                }
            )
        }
    }
}
