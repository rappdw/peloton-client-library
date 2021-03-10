import logging
from .api import find_last_workout
from .peloton import PelotonUser, PelotonWorkout, PelotonWorkoutMetricsFactory
from .config import get_logger

def refresh():
    get_logger().setLevel(logging.INFO)
    workouts = PelotonWorkout.list(last_id=find_last_workout())
    get_logger().info(f"Found {len(workouts)} since the last workout we've cached")
    # because the list call doesn't provide fields like leaderboard rank, achievements, etc., call
    # PelotonWorkout.get() for each workout in the list. This will fill out the remaining fields
    #
    # also, retrieve the metrics for each workout
    for workout in workouts:
        if hasattr(workout.ride, 'instructor'):
            get_logger().info(f'{workout.start_time} - {workout.ride.title} with {workout.ride.instructor}')
        else:
            get_logger().info(f'{workout.start_time} - {workout.ride.title}')
        PelotonWorkout.get(workout.id)
        PelotonWorkoutMetricsFactory.get(workout.id)

    # retrieve my user record as well
    PelotonUser.me()
