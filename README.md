# pandemic-xai-player
 
# Pandemic XAI Player

A simulation game inspired by Pandemic: Hot Zone – Europe. This project integrates a Gymnasium-compatible environment with game logic, graphical rendering using NetworkX and Matplotlib, and a Greedy Agent for automated gameplay.

## Features

- **Game Environment:** Built using [Gymnasium](https://gymnasium.farama.org/) for reinforcement learning simulations.
- **Graphical Rendering:** Uses NetworkX and Matplotlib to visualize cities, player positions, infection levels, and game events.
- **Agent-Based Gameplay:** Includes a Greedy Agent that evaluates game states with custom heuristics defined in `state_eval.py`.
- **Modular Design:** Codebase is organized into separate modules for constants, board logic, location management, player actions, rendering, and agent behavior.

## Project Structure

- **constants.py:** Contains configurations for cities, positions, colors, and connections.
- **board.py:** Manages the game board state including player decks, infection events, and outbreak logic.
- **location.py:** Defines the `City` class which represents each city in the game.
- **player.py:** Implements the `Player` class including actions like movement, treating infections, and sharing knowledge.
- **render.py / Render.py:** Provides rendering functionality for the game map and visual display of game state.
- **env.py:** Implements a Gymnasium-compatible environment for integrating the game with reinforcement learning frameworks.
- **greedy.py:** Contains the Greedy Agent that selects actions based on heuristic evaluations.
- **state_eval.py:** Contains functions to compute heuristic values for game state evaluation.
- **README.md:** This documentation file.
- **.gitignore & .gitattributes:** Git configuration files.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ricardocsantana/pandemic-xai-player.git
   cd pandemic-xai-player
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use: env\Scripts\activate
   ```

3. **Install dependencies:**

   Create a `requirements.txt` file if not already provided. Suggested packages include:
   - gymnasium
   - networkx
   - matplotlib
   - numpy

   Then run:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the simulation with the Greedy Agent:
```bash
python main.py
```

## Running Tests

To execute unit tests, run:
```bash
python tests.py
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
- Please ensure your code follows the project conventions.
- Write tests for new functionalities.

## License

This project is open-source. *(Include your chosen license information here.)*

## Acknowledgments

- Inspired by the popular board game Pandemic.
- Built for learning and experimentation in AI and Reinforcement Learning.