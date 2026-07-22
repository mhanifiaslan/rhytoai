package ai.rytho.presentation.face_analysis

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.rytho.domain.model.FaceAnalysisResult
import ai.rytho.domain.repository.FaceAnalysisRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

sealed class FaceAnalysisState {
    object Idle : FaceAnalysisState()
    object Loading : FaceAnalysisState()
    data class Success(val result: FaceAnalysisResult) : FaceAnalysisState()
    data class Error(val message: String) : FaceAnalysisState()
}

@HiltViewModel
class FaceAnalysisViewModel @Inject constructor(
    private val repository: FaceAnalysisRepository
) : ViewModel() {

    private val _state = MutableStateFlow<FaceAnalysisState>(FaceAnalysisState.Idle)
    val state: StateFlow<FaceAnalysisState> = _state.asStateFlow()

    fun analyzeImage(file: File) {
        viewModelScope.launch {
            _state.value = FaceAnalysisState.Loading
            repository.analyzeFace(file).fold(
                onSuccess = { result ->
                    _state.value = FaceAnalysisState.Success(result)
                },
                onFailure = { exception ->
                    _state.value = FaceAnalysisState.Error(exception.message ?: "An unknown error occurred")
                }
            )
        }
    }
    
    fun reset() {
        _state.value = FaceAnalysisState.Idle
    }
}
