from database.repositories.gamification import (
    ACHIEVEMENT_META,
    LEAGUE_CONFIG,
    check_and_grant_streak_achievements,
    get_leaderboard,
    get_user_achievements,
    grant_achievement,
    next_league,
    streak_to_league,
    upsert_user_league,
)
from database.repositories.tracking import (
    get_current_streak,
    get_streak_leaderboard,
    get_today_tracking,
    get_tracking_by_date,
    upsert_tracking,
)
from database.repositories.users import create_user, get_or_create_user, get_user
from database.repositories.profiles import (
    create_profile_version,
    get_latest_profile,
    save_skin_analysis,
    update_analysis_user_confirmation,
)
from database.repositories.routines import (
    create_routine,
    get_latest_routine,
    get_routine_products,
    set_routine_product,
)
from database.repositories.reminders import (
    get_all_active_reminders,
    get_reminder,
    upsert_reminder,
)
from database.repositories.products import (
    add_catalog_product,
    add_user_product,
    get_active_products,
    get_catalog_product,
    get_ingredient_by_inci,
    get_ingredients_bulk,
    get_user_scans,
    increment_scan_count,
    remove_user_product,
    save_product_scan,
    search_catalog,
)
