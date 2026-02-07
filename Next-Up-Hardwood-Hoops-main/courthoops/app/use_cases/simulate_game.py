from courthoops.domain.game.state import GameState
from courthoops.simulation.engine.game_engine import GameEngine


def simulate_game(game_engine: GameEngine, game_state: GameState):
    """Runs a single game simulation and returns emitted events."""
    return list(game_engine.simulate(game_state))


