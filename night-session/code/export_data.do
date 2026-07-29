version 17.0
clear all
set more off
set seed 20260721

global out "../data"

capture mkdir "$out"

set obs 50
gen state = _n
gen treated = state <= 35
gen adopt_year = 2006 + floor((state - 1) / 4) if treated
replace adopt_year = 2014 if adopt_year > 2014 & treated
gen state_fe = rnormal(0, 1.8)
gen state_slope = rnormal(0, 0.025)

expand 20
bysort state: gen year = 1999 + _n
gen event_time = year - adopt_year if treated

gen true_effect = 0
replace true_effect = -0.25 if event_time == 0
replace true_effect = -0.50 if event_time == 1
replace true_effect = -0.75 if event_time == 2
replace true_effect = -1.00 if event_time >= 3 & event_time < .

gen common_trend = 0.08 * (year - 2000)
gen y0 = 55 + state_fe + state_slope * (year - 2000) + common_trend + rnormal(0, 0.55)
gen teen_employment_rate = y0 + true_effect
gen teen_employment_rate_s1 = teen_employment_rate + 0.11 * treated * (year - 2000)
gen post_adoption = treated & year >= adopt_year

tempfile base
save `base', replace

* S0 clean panel
use `base', clear
order state year treated adopt_year event_time teen_employment_rate true_effect post_adoption
export delimited using "${out}/panel_s0.csv", replace

quietly count
local n_before = r(N)
quietly count if treated
local treated_before = r(N)
quietly count if !treated
local never_before = r(N)

* S1 differential trends panel
use `base', clear
keep state year treated adopt_year event_time teen_employment_rate_s1 true_effect post_adoption
rename teen_employment_rate_s1 teen_employment_rate
export delimited using "${out}/panel_s1.csv", replace

* Policy ledger
use `base', clear
collapse (first) treated adopt_year, by(state)
export delimited using "${out}/policy_ledger.csv", replace

* Raw merge inputs
use `base', clear
gen str6 state_id = "ST" + string(state, "%02.0f")
gen str7 state_code = state_id
replace state_code = state_id + "X" if treated & year >= 2010
gen teen_employment_count = round(teen_employment_rate * 1000)
gen population_weight = 0.85 + mod(state, 7) * 0.02
export delimited state_id year teen_employment_count using "${out}/employment_raw.csv", replace
export delimited state_code year population_weight using "${out}/population_weights.csv", replace

* S2 selective merge loss
use `base', clear
gen keep_after_merge = 1
gen draw = runiform()
replace keep_after_merge = 0 if treated & teen_employment_rate < 55 & draw < 0.28
keep if keep_after_merge
order state year treated adopt_year event_time teen_employment_rate true_effect post_adoption
export delimited using "${out}/panel_s2.csv", replace

quietly count
local n_after = r(N)
quietly count if treated
local treated_after = r(N)
quietly count if !treated
local never_after = r(N)

clear
set obs 3
gen str16 group = ""
replace group = "adopting" in 1
replace group = "never_treated" in 2
replace group = "total" in 3
gen n_state_years = .
replace n_state_years = `treated_before' in 1
replace n_state_years = `never_before' in 2
replace n_state_years = `n_before' in 3
export delimited using "${out}/row_ledger_s0.csv", replace

clear
set obs 3
gen str16 group = ""
replace group = "adopting" in 1
replace group = "never_treated" in 2
replace group = "total" in 3
gen n_state_years = .
replace n_state_years = `treated_after' in 1
replace n_state_years = `never_after' in 2
replace n_state_years = `n_after' in 3
export delimited using "${out}/row_ledger_s2.csv", replace

clear
set obs 9
gen event_time = .
local i = 1
foreach k in -4 -3 -2 0 1 2 3 4 5 {
    replace event_time = `k' in `i'
    local ++i
}
gen true_effect_pp = cond(event_time < 0, 0, cond(event_time==0,-0.25,cond(event_time==1,-0.50,cond(event_time==2,-0.75,-1.00))))
export delimited using "${out}/answer_key_effects.csv", replace

display "EXPORTED before=`n_before' after=`n_after' adopting `treated_before'->`treated_after' never=`never_before'"
