from typing import Tuple

import pandas as pd
import pygeos


def compute_individual_velocity(
    traj_data: pd.DataFrame, frame_rate: float, frame_step: int
) -> pd.DataFrame:
    """Compute the individual velocity for each pedestrian

    Args:
        traj_data (TrajectoryData): trajectory data
        frame_rate (float): frame rate of the trajectory
        frame_step (int): gives the size of time interval for calculating the velocity

    Returns:
        DataFrame containing the columns 'ID', 'frame', 'speed'
    """
    df_movement = _compute_individual_movement(traj_data, frame_step)
    df_speed = _compute_individual_speed(df_movement, frame_rate)

    return df_speed


def compute_mean_velocity_per_frame(
    traj_data: pd.DataFrame, frame_rate: float, frame_step: int
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute mean velocity per frame

    Args:
        traj_data (TrajectoryData): trajectory data
        frame_rate (float): frame rate of the trajectory
        frame_step (int): gives the size of time interval for calculating the velocity

    Returns:
        DataFrame containing the columns 'frame' and 'speed' and
        DataFrame containing the columns 'ID', 'frame', 'speed' and
    """
    df_speed = compute_individual_velocity(traj_data, frame_rate, frame_step)
    df_mean = df_speed.groupby("frame")["speed"].mean()
    df_mean = df_mean.reindex(
        list(range(traj_data.frame.min(), traj_data.frame.max() + 1)),
        fill_value=0.0,
    )
    return df_mean, df_speed


def _compute_individual_movement(traj_data: pd.DataFrame, frame_step: int) -> pd.DataFrame:
    """Compute the individual movement in the time interval frame_step

    The movement is computed for the interval [frame - frame_step: frame + frame_step], if one of
    the boundaries is not contained in the trajectory frame will be used as boundary. Hence, the
    intervals become [frame, frame + frame_step], or [frame - frame_step, frame] respectively.

    Args:
        traj_data (pd.DataFrame): trajectory data
        frame_step (int): how frames back and forwards are used to compute the movement

    Returns:
        DataFrame containing the columns: 'ID', 'frame', 'start', 'end', 'start_frame, and
        'end_frame'. Where 'start'/'end' are the points where the movement start/ends, and
        'start_frame'/'end_frame' are the corresponding frames.
    """
    df_movement = traj_data.copy(deep=True)

    df_movement["start"] = (
        df_movement.groupby("ID")["points"].shift(frame_step).fillna(df_movement["points"])
    )
    df_movement["end"] = (
        df_movement.groupby("ID")["points"].shift(-frame_step).fillna(df_movement["points"])
    )
    df_movement["start_frame"] = (
        df_movement.groupby("ID")["frame"].shift(frame_step).fillna(df_movement["frame"])
    )
    df_movement["end_frame"] = (
        df_movement.groupby("ID")["frame"].shift(-frame_step).fillna(df_movement["frame"])
    )

    return df_movement[["ID", "frame", "start", "end", "start_frame", "end_frame"]]


def _compute_individual_speed(movement_data: pd.DataFrame, frame_rate: float) -> pd.DataFrame:
    """Compute the instantaneous velocity of each pedestrian.

    Args:
        movement_data (pd.DataFrame): movement data (see compute_individual_movement)
        frame_rate (float): frame rate of the trajectory data

    Returns:
        DataFrame containing the columns: 'ID', 'frame', and 'speed' with the speed in m/s
    """
    movement_data["distance"] = pygeos.distance(movement_data["start"], movement_data["end"])
    movement_data["speed"] = movement_data["distance"] / (
        (movement_data["end_frame"] - movement_data["start_frame"]) / frame_rate
    )

    return movement_data[["ID", "frame", "speed"]]
