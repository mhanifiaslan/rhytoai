package ai.rytho.presentation.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavController
import androidx.navigation.compose.currentBackStackEntryAsState

sealed class BottomNavItem(val route: String, val title: String, val icon: ImageVector) {
    object Home : BottomNavItem("home", "Ana Sayfa", Icons.Default.Home)
    object Astrology : BottomNavItem("astrology", "Harita 🔮", Icons.Default.Star)
    object Chat : BottomNavItem("chat", "AI Chat ✦", Icons.Default.Email)
    object Social : BottomNavItem("social", "Sosyal 🌐", Icons.Default.Share)
    object Profile : BottomNavItem("profile", "Profil 👤", Icons.Default.Person)
}

@Composable
fun CosmicBottomNavigationBar(navController: NavController) {
    val items = listOf(
        BottomNavItem.Home,
        BottomNavItem.Astrology,
        BottomNavItem.Chat,
        BottomNavItem.Social,
        BottomNavItem.Profile
    )

    val navBackStackEntry = navController.currentBackStackEntryAsState().value
    val currentRoute = navBackStackEntry?.destination?.route

    NavigationBar(
        containerColor = Color(0xFF15121B),
        contentColor = Color(0xFFE7E0ED)
    ) {
        items.forEach { item ->
            val selected = currentRoute == item.route
            NavigationBarItem(
                selected = selected,
                onClick = {
                    if (currentRoute != item.route) {
                        navController.navigate(item.route) {
                            popUpTo(navController.graph.startDestinationId) {
                                saveState = true
                            }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                },
                icon = {
                    Icon(
                        item.icon,
                        contentDescription = item.title,
                        tint = if (selected) Color(0xFF8B5CF6) else Color(0xFF7A7090)
                    )
                },
                label = {
                    Text(
                        item.title,
                        color = if (selected) Color(0xFF8B5CF6) else Color(0xFF7A7090)
                    )
                },
                colors = NavigationBarItemDefaults.colors(
                    indicatorColor = Color(0xFF231F30)
                )
            )
        }
    }
}
