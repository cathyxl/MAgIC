from .base import Environment, TimeStep
from .chameleon_competition import Chameleon_Competition
from .chameleon_competition_pgm import Chameleon_Competition_PGM

from .undercover_competition import Undercover_Competition
from .undercover_competition_pgm import Undercover_Competition_PGM

from .airportfee import Airport_Fee_Allocation
from .airportfee_pgm import Airport_Fee_Allocation_PGM

from .prisoner import Prinsoner_Dilemma
from .prisoner_pgm import Prinsoner_Dilemma_PGM

from .public_good import Public_Good
from .public_good_pgm import Public_Good_PGM


from ..config import EnvironmentConfig

ALL_ENVIRONMENTS = [
    Chameleon_Competition,
    Chameleon_Competition_PGM,
    Undercover_Competition,
    Undercover_Competition_PGM,
    Airport_Fee_Allocation,
    Airport_Fee_Allocation_PGM,
    Prinsoner_Dilemma,
    Prinsoner_Dilemma_PGM,
    Public_Good,
    Public_Good_PGM,
]

ENV_REGISTRY = {env.type_name: env for env in ALL_ENVIRONMENTS}

# print(ENV_REGISTRY)
# Load an environment from a config dictionary
def load_environment(config: EnvironmentConfig):
    try:
        env_cls = ENV_REGISTRY[config["env_type"]]
    except KeyError:
        raise ValueError(f"Unknown environment type: {config['env_type']}")
    print(config)
    env = env_cls.from_config(config)
    return env
