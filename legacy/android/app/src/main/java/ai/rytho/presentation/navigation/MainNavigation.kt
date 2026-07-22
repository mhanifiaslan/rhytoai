package ai.rytho.presentation.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument

import ai.rytho.domain.repository.UserRepository
import ai.rytho.presentation.auth.AuthState
import ai.rytho.presentation.auth.AuthViewModel
import ai.rytho.presentation.auth.LoginScreen
import ai.rytho.presentation.home.HomeScreen
import ai.rytho.presentation.chat.ChatScreen
import ai.rytho.presentation.astrology.AstrologyScreen
import ai.rytho.presentation.social.SocialScreen
import ai.rytho.presentation.profile.ProfileScreen
import ai.rytho.presentation.face_analysis.FaceAnalysisScreen
import ai.rytho.presentation.onboarding.OnboardingScreen

@Composable
fun MainNavigation(
    authViewModel: AuthViewModel = hiltViewModel(),
    userRepository: UserRepository = hiltViewModel<AuthViewModel>().let { hiltViewModel<OnboardingViewModelWrapper>().userRepository }
) {
    val authState by authViewModel.authState.collectAsState()
    val navController = rememberNavController()

    when (authState) {
        is AuthState.Loading -> {
            // Splash / Loading
        }
        is AuthState.Unauthenticated, is AuthState.Error -> {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate("home") {
                        popUpTo(navController.graph.id) { inclusive = true }
                    }
                }
            )
        }
        is AuthState.Authenticated -> {
            val user = (authState as AuthState.Authenticated).user
            val navBackStackEntry by navController.currentBackStackEntryAsState()
            val currentRoute = navBackStackEntry?.destination?.route ?: ""

            var isOnboardingChecked by remember { mutableStateOf(false) }
            var needsOnboarding by remember { mutableStateOf(false) }

            LaunchedEffect(user.uid) {
                userRepository.getUserProfile(user.uid).fold(
                    onSuccess = { profile ->
                        needsOnboarding = profile == null || !profile.onboardingCompleted
                        isOnboardingChecked = true
                    },
                    onFailure = {
                        needsOnboarding = true
                        isOnboardingChecked = true
                    }
                )
            }

            if (!isOnboardingChecked) {
                return
            }

            val startDest = if (needsOnboarding) "onboarding" else "home"
            val mainTabRoutes = listOf("home", "astrology", "chat", "social", "profile")
            val showBottomBar = mainTabRoutes.any { currentRoute.startsWith(it) }

            Scaffold(
                bottomBar = {
                    if (showBottomBar) {
                        CosmicBottomNavigationBar(navController = navController)
                    }
                }
            ) { paddingValues ->
                NavHost(
                    navController = navController,
                    startDestination = startDest,
                    modifier = Modifier.padding(paddingValues)
                ) {
                    composable("onboarding") {
                        OnboardingScreen(
                            onOnboardingComplete = {
                                navController.navigate("home") {
                                    popUpTo("onboarding") { inclusive = true }
                                }
                            }
                        )
                    }
                    composable("home") {
                        HomeScreen(
                            user = user,
                            onNavigateToChat = { navController.navigate("chat") },
                            onNavigateToFaceAnalysis = { navController.navigate("face_analysis") },
                            onNavigateToIChing = { navController.navigate("iching") },
                            onNavigateToAstrology = { navController.navigate("astrology") }
                        )
                    }
                    composable("chat") {
                        ChatScreen(
                            onNavigateBack = { navController.popBackStack() },
                            canNavigateBack = false
                        )
                    }
                    composable(
                        route = "chat?initialReading={initialReading}",
                        arguments = listOf(navArgument("initialReading") {
                            type = NavType.StringType
                            nullable = true
                            defaultValue = null
                        })
                    ) {
                        ChatScreen(
                            onNavigateBack = { navController.popBackStack() },
                            canNavigateBack = true
                        )
                    }
                    composable("astrology") {
                        AstrologyScreen()
                    }
                    composable("social") {
                        SocialScreen()
                    }
                    composable("profile") {
                        ProfileScreen(
                            user = user,
                            onSignOut = { authViewModel.signOut() },
                            onNavigateToFaceAnalysis = { navController.navigate("face_analysis") },
                            onNavigateToIChing = { navController.navigate("iching") },
                            onNavigateToSettings = { navController.navigate("settings") }
                        )
                    }
                    composable("face_analysis") {
                        FaceAnalysisScreen(
                            onNavigateBack = { navController.popBackStack() },
                            onNavigateToChat = { summary ->
                                val encoded = java.net.URLEncoder.encode(summary, "UTF-8")
                                navController.navigate("chat?initialReading=$encoded")
                            }
                        )
                    }
                    composable("iching") {
                        ai.rytho.presentation.iching.IChingScreen()
                    }
                    composable("settings") {
                        ai.rytho.presentation.settings.SettingsScreen(
                            onNavigateBack = { navController.popBackStack() },
                            onSignOut = { authViewModel.signOut() }
                        )
                    }
                }
            }
        }
    }
}

@dagger.hilt.android.lifecycle.HiltViewModel
class OnboardingViewModelWrapper @javax.inject.Inject constructor(
    val userRepository: UserRepository
) : androidx.lifecycle.ViewModel()
