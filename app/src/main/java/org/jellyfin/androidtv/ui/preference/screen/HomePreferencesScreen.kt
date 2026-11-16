package org.jellyfin.androidtv.ui.preference.screen

import org.jellyfin.androidtv.R
import org.jellyfin.androidtv.constant.HomeSectionType
import org.jellyfin.androidtv.preference.UserPreferences
import org.jellyfin.androidtv.preference.UserSettingPreferences
import org.jellyfin.androidtv.ui.preference.dsl.OptionsFragment
import org.jellyfin.androidtv.ui.preference.dsl.enum
import org.jellyfin.androidtv.ui.preference.dsl.list
import org.jellyfin.androidtv.ui.preference.dsl.optionsScreen
import org.jellyfin.androidtv.util.getQuantityString
import org.jellyfin.preference.store.PreferenceStore
import org.koin.android.ext.android.inject

class HomePreferencesScreen : OptionsFragment() {
	private val userSettingPreferences: UserSettingPreferences by inject()
	private val userPreferences: UserPreferences by inject()

	override val stores: Array<PreferenceStore<*, *>>
		get() = arrayOf(userSettingPreferences)

	override val screen by optionsScreen {
		setTitle(R.string.home_prefs)

		category {
			setTitle(R.string.home_sections)

			userSettingPreferences.homesections.forEachIndexed { index, section ->
				enum<HomeSectionType> {
					title = getString(R.string.home_section_i, index + 1)
					bind(userSettingPreferences, section)
				}
			}
		}

		category {
			setTitle(R.string.lbl_next_up)

			@Suppress("MagicNumber")
			list {
				setTitle(R.string.home_next_up_max_days)

				entries = buildMap {
					put("0", getString(R.string.home_next_up_max_days_disabled))
					listOf(7, 14, 30, 60, 90, 180, 365).forEach { days ->
						put(days.toString(), context.getQuantityString(R.plurals.days, days))
					}
				}

				bind {
					get { userPreferences[UserPreferences.homeNextUpMaxDays].toString() }
					set { value -> userPreferences[UserPreferences.homeNextUpMaxDays] = value.toInt() }
					default { UserPreferences.homeNextUpMaxDays.defaultValue.toString() }
				}
			}
		}
	}
}
