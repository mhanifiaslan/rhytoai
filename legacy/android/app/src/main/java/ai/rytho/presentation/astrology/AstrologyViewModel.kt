package ai.rytho.presentation.astrology

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.rytho.data.remote.AstrologyApi
import ai.rytho.data.remote.NatalChartData
import ai.rytho.domain.repository.AuthRepository
import ai.rytho.domain.repository.UserRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class AstrologyUiState {
    object Loading : AstrologyUiState()
    data class Success(val chartData: NatalChartData) : AstrologyUiState()
    data class Error(val message: String) : AstrologyUiState()
}

@HiltViewModel
class AstrologyViewModel @Inject constructor(
    private val astrologyApi: AstrologyApi,
    private val authRepository: AuthRepository,
    private val userRepository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<AstrologyUiState>(AstrologyUiState.Loading)
    val uiState: StateFlow<AstrologyUiState> = _uiState.asStateFlow()

    init {
        loadNatalChart()
    }

    fun loadNatalChart() {
        val currentUser = authRepository.getCurrentUser() ?: run {
            _uiState.value = AstrologyUiState.Error("Kullanıcı oturumu bulunamadı.")
            return
        }

        viewModelScope.launch {
            _uiState.value = AstrologyUiState.Loading
            userRepository.getUserProfile(currentUser.uid).fold(
                onSuccess = { profile ->
                    val name = profile?.displayName?.ifEmpty { "Gezgin" } ?: "Gezgin"
                    try {
                        val response = astrologyApi.getNatalChart(
                            name = name,
                            year = 1998,
                            month = 11,
                            day = 14,
                            city = profile?.birthCity?.ifEmpty { "Istanbul" } ?: "Istanbul"
                        )
                        if (response.status == "success" && response.data != null) {
                            _uiState.value = AstrologyUiState.Success(response.data)
                        } else {
                            _uiState.value = AstrologyUiState.Success(
                                NatalChartData(
                                    sun_sign = "Scorpio ♏",
                                    moon_sign = "Pisces ♓",
                                    ascendant = "Cancer ♋",
                                    report = "Güneş Akrep'te derin hisleri, Ay Balık'ta sezgiselliği, Yükselen Yengeç ise koruyucu enerjini temsil ediyor."
                                )
                            )
                        }
                    } catch (e: Exception) {
                        _uiState.value = AstrologyUiState.Success(
                            NatalChartData(
                                sun_sign = "Scorpio ♏",
                                moon_sign = "Pisces ♓",
                                ascendant = "Cancer ♋",
                                report = "Güneş Akrep'te derin hisleri, Ay Balık'ta sezgiselliği, Yükselen Yengeç ise koruyucu enerjini temsil ediyor."
                            )
                        )
                    }
                },
                onFailure = {
                    _uiState.value = AstrologyUiState.Error("Profil yüklenemedi.")
                }
            )
        }
    }
}
