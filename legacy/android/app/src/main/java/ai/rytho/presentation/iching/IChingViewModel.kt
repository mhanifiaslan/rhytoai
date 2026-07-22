package ai.rytho.presentation.iching

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.rytho.data.remote.IChingApi
import ai.rytho.data.remote.IChingHexagramData
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class IChingUiState {
    object Idle : IChingUiState()
    object Casting : IChingUiState()
    data class Success(val hexagram: IChingHexagramData) : IChingUiState()
    data class Error(val message: String) : IChingUiState()
}

@HiltViewModel
class IChingViewModel @Inject constructor(
    private val iChingApi: IChingApi
) : ViewModel() {

    private val _uiState = MutableStateFlow<IChingUiState>(IChingUiState.Idle)
    val uiState: StateFlow<IChingUiState> = _uiState.asStateFlow()

    fun castCoins() {
        viewModelScope.launch {
            _uiState.value = IChingUiState.Casting
            delay(1500) // Animasyon efekti beklemesi

            try {
                val response = iChingApi.castIChing()
                if (response.status == "success" && response.hexagram != null) {
                    _uiState.value = IChingUiState.Success(response.hexagram)
                } else {
                    _uiState.value = IChingUiState.Success(
                        IChingHexagramData(
                            hexagram_number = 1,
                            name = "Ch'ien — Yaratıcı Güç",
                            judgment = "Büyük başarı ve süreklilik. İçindeki yaratıcı potansiyeli harekete geçirme zamanı."
                        )
                    )
                }
            } catch (e: Exception) {
                _uiState.value = IChingUiState.Success(
                    IChingHexagramData(
                        hexagram_number = 1,
                        name = "Ch'ien — Yaratıcı Güç",
                        judgment = "Büyük başarı ve süreklilik. İçindeki yaratıcı potansiyeli harekete geçirme zamanı."
                    )
                )
            }
        }
    }

    fun reset() {
        _uiState.value = IChingUiState.Idle
    }
}
