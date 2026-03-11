class ScenarioManager:
    SCENARIOS = {
        'NORMAL': {
            'arrival_rate_multiplier': 1.0,
            'staff_multiplier': 1.0,
            'icu_probability_multiplier': 1.0,
            'description': "Standard day-to-day operations."
        },
        'FLU_SURGE': {
            'arrival_rate_multiplier': 2.0,
            'staff_multiplier': 0.9, # Some staff sick
            'icu_probability_multiplier': 1.2, # Sicker patients
            'description': "Seasonal flu outbreak. High volume, moderate severity."
        },
        'MASS_CASUALTY': {
            'arrival_rate_multiplier': 5.0, # Huge spike
            'staff_multiplier': 1.0,
            'icu_probability_multiplier': 2.0, # High trauma
            'description': "Major accident or disaster. Extreme volume and severity."
        },
        'STAFF_SHORTAGE': {
            'arrival_rate_multiplier': 1.0,
            'staff_multiplier': 0.6, # Strike or sickness
            'icu_probability_multiplier': 1.0,
            'description': "Critical staffing levels."
        }
    }

    @staticmethod
    def get_config(scenario_name, base_config):
        """
        Applies scenario modifiers to the base configuration.
        """
        scenario = ScenarioManager.SCENARIOS.get(scenario_name, ScenarioManager.SCENARIOS['NORMAL'])
        
        # Apply Modifiers
        new_config = base_config.copy()
        new_config['arrival_rate'] = base_config.get('arrival_rate', 0.5) * scenario['arrival_rate_multiplier']
        
        # Staff is usually an integer count in base_config, need to apply multiplier
        # We might need to handle this in the HospitalSim init if we pass raw numbers.
        # But here we return a config dict.
        if 'staff' in new_config:
            new_config['staff'] = int(new_config['staff'] * scenario['staff_multiplier'])
            
        # Store scenario metadata
        new_config['scenario_name'] = scenario_name
        new_config['icu_prob_mult'] = scenario['icu_probability_multiplier']
        
        print(f"🔹 Applied Scenario: {scenario_name}")
        print(f"   - Arrival Rate: {new_config['arrival_rate']}")
        print(f"   - Staff: {new_config['staff']}")
        
        return new_config
