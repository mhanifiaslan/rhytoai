package ai.rytho.presentation.onboarding

import androidx.compose.animation.AnimatedContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun OnboardingScreen(
    onOnboardingComplete: () -> Unit,
    viewModel: OnboardingViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(uiState.isCompleted) {
        if (uiState.isCompleted) {
            onOnboardingComplete()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0F0C1B))
    ) {
        // Glowing Orbs Background
        Box(
            modifier = Modifier
                .size(280.dp)
                .align(Alignment.TopEnd)
                .offset(x = 60.dp, y = (-40).dp)
                .blur(90.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFF8B5CF6).copy(alpha = 0.4f), Color.Transparent)
                    ),
                    shape = CircleShape
                )
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .systemBarsPadding()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Header Progress Dots
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                modifier = Modifier.padding(top = 16.dp)
            ) {
                repeat(4) { index ->
                    val active = index + 1 == uiState.step
                    Box(
                        modifier = Modifier
                            .height(4.dp)
                            .width(if (active) 32.dp else 12.dp)
                            .background(
                                color = if (active) Color(0xFF8B5CF6) else Color(0xFF2E273F),
                                shape = RoundedCornerShape(2.dp)
                            )
                    )
                }
            }

            // Step Content Animated
            AnimatedContent(
                targetState = uiState.step,
                label = "onboarding_steps"
            ) { step ->
                when (step) {
                    1 -> StepWelcome()
                    2 -> StepGender(
                        selectedGender = uiState.gender,
                        onGenderSelect = {
                            viewModel.updateGender(it)
                            viewModel.nextStep()
                        }
                    )
                    3 -> StepBirthDateTime(
                        birthDate = uiState.birthDate,
                        birthTime = uiState.birthTime,
                        onDateChange = { viewModel.updateBirthDate(it) },
                        onTimeChange = { viewModel.updateBirthTime(it) },
                        onNext = { viewModel.nextStep() }
                    )
                    4 -> StepBirthCity(
                        birthCity = uiState.birthCity,
                        onCityChange = { viewModel.updateBirthCity(it) },
                        onDone = { viewModel.nextStep() }
                    )
                }
            }

            // Error display if any
            if (uiState.error != null) {
                Text(
                    text = uiState.error!!,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall,
                    textAlign = TextAlign.Center
                )
            }

            // Bottom Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (uiState.step > 1) {
                    TextButton(onClick = { viewModel.previousStep() }) {
                        Text("Geri", color = Color(0xFF7A7090))
                    }
                } else {
                    Spacer(modifier = Modifier.width(48.dp))
                }

                Button(
                    onClick = { viewModel.nextStep() },
                    enabled = !uiState.isLoading,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7C3AED)),
                    shape = RoundedCornerShape(16.dp),
                    modifier = Modifier
                        .height(50.dp)
                        .padding(horizontal = 16.dp)
                ) {
                    if (uiState.isLoading) {
                        CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp))
                    } else {
                        Text(
                            text = if (uiState.step == 4) "Tamamla ✦" else "Devam Et",
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun StepWelcome() {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.padding(16.dp)
    ) {
        Text(text = "✦", fontSize = 56.sp, color = Color(0xFFD4AF37))
        Spacer(modifier = Modifier.height(24.dp))
        Text(
            text = "Kozmik Haritana Yolculuk Başlıyor",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = Color(0xFFE7E0ED),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = "Yıldızların, gezegenlerin ve yüzündeki kadim hatların senin için çizdiği eşsiz hikayeyi keşfetmeye hazır mısın?",
            style = MaterialTheme.typography.bodyMedium,
            color = Color(0xFF9B8FAE),
            textAlign = TextAlign.Center,
            lineHeight = 22.sp
        )
    }
}

@Composable
fun StepGender(
    selectedGender: String,
    onGenderSelect: (String) -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.fillMaxWidth().padding(16.dp)
    ) {
        Text(
            text = "Cinsiyetini Seç",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = Color(0xFFE7E0ED),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Yüz analizi ve BaZi haritası mizaç dengelemesi için.",
            style = MaterialTheme.typography.bodyMedium,
            color = Color(0xFF9B8FAE),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(32.dp))

        val options = listOf("Kadın ♀", "Erkek ♂", "Belirtmek İstemiyorum ✨")
        options.forEach { option ->
            val isSelected = selectedGender == option
            OutlinedButton(
                onClick = { onGenderSelect(option) },
                modifier = Modifier.fillMaxWidth().height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.outlinedButtonColors(
                    containerColor = if (isSelected) Color(0xFF8B5CF6).copy(alpha = 0.2f) else Color(0xFF15121B)
                ),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (isSelected) Color(0xFF8B5CF6) else Color(0xFF2E273F)
                )
            ) {
                Text(option, color = Color(0xFFE7E0ED), fontWeight = FontWeight.SemiBold)
            }
            Spacer(modifier = Modifier.height(12.dp))
        }
    }
}

@Composable
fun StepBirthDateTime(
    birthDate: String,
    birthTime: String,
    onDateChange: (String) -> Unit,
    onTimeChange: (String) -> Unit,
    onNext: () -> Unit
) {
    val focusManager = LocalFocusManager.current

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.fillMaxWidth().padding(16.dp)
    ) {
        Text(
            text = "Doğum Tarihi & Saatin",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = Color(0xFFE7E0ED),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Gezegenlerin ve yükselen burcunun hassas konumlanması için gerekli.",
            style = MaterialTheme.typography.bodyMedium,
            color = Color(0xFF9B8FAE),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(32.dp))

        // Auto-formatted Birth Date
        OutlinedTextField(
            value = birthDate,
            onValueChange = { input ->
                val digits = input.filter { it.isDigit() }.take(8)
                val formatted = formatDateString(digits)
                onDateChange(formatted)
            },
            label = { Text("Doğum Tarihi (GG.AA.YYYY)") },
            placeholder = { Text("14.11.1998") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Number,
                imeAction = ImeAction.Next
            ),
            keyboardActions = KeyboardActions(
                onNext = { focusManager.moveFocus(FocusDirection.Down) }
            ),
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Color(0xFF8B5CF6),
                unfocusedBorderColor = Color(0xFF2E273F),
                focusedTextColor = Color(0xFFE7E0ED),
                unfocusedTextColor = Color(0xFFE7E0ED)
            )
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Auto-formatted Birth Time
        OutlinedTextField(
            value = birthTime,
            onValueChange = { input ->
                val digits = input.filter { it.isDigit() }.take(4)
                val formatted = formatTimeString(digits)
                onTimeChange(formatted)
            },
            label = { Text("Doğum Saati (SS:DK)") },
            placeholder = { Text("14:30") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Number,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = {
                    focusManager.clearFocus()
                    onNext()
                }
            ),
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Color(0xFF8B5CF6),
                unfocusedBorderColor = Color(0xFF2E273F),
                focusedTextColor = Color(0xFFE7E0ED),
                unfocusedTextColor = Color(0xFFE7E0ED)
            )
        )
    }
}

@Composable
fun StepBirthCity(
    birthCity: String,
    onCityChange: (String) -> Unit,
    onDone: () -> Unit
) {
    val focusManager = LocalFocusManager.current

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.fillMaxWidth().padding(16.dp)
    ) {
        Text(
            text = "Doğduğun Şehir",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = Color(0xFFE7E0ED),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Enlem ve boylamınız coğrafi ev hesaplamaları için kullanılacak.",
            style = MaterialTheme.typography.bodyMedium,
            color = Color(0xFF9B8FAE),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(32.dp))

        OutlinedTextField(
            value = birthCity,
            onValueChange = onCityChange,
            label = { Text("Şehir veya Ülke") },
            placeholder = { Text("İstanbul, Türkiye") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Text,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = {
                    focusManager.clearFocus()
                    onDone()
                }
            ),
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = Color(0xFF8B5CF6),
                unfocusedBorderColor = Color(0xFF2E273F),
                focusedTextColor = Color(0xFFE7E0ED),
                unfocusedTextColor = Color(0xFFE7E0ED)
            )
        )
    }
}

// Helper functions to auto-format Date and Time
private fun formatDateString(digits: String): String {
    return buildString {
        for (i in digits.indices) {
            append(digits[i])
            if ((i == 1 || i == 3) && i != digits.lastIndex) {
                append('.')
            }
        }
    }
}

private fun formatTimeString(digits: String): String {
    return buildString {
        for (i in digits.indices) {
            append(digits[i])
            if (i == 1 && i != digits.lastIndex) {
                append(':')
            }
        }
    }
}
