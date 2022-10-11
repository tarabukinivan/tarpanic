import logging
import time
from http.client import IncompleteRead
from json import JSONDecodeError

from requests.exceptions import ConnectionError as ReqConnectionError, \
    ReadTimeout, ChunkedEncodingError
from urllib3.exceptions import ProtocolError

from src.alerting.alerts.alerts import CouldNotFindLiveFullNodeAlert, \
    ErrorWhenReadingDataFromNode, CannotAccessGitHubPageAlert
from src.monitoring.monitors.github import GitHubMonitor
from src.monitoring.monitors.network import NetworkMonitor
from src.monitoring.monitors.node import NodeMonitor
from src.utils.config_parsers.internal import InternalConfig
from src.utils.config_parsers.internal_parsed import InternalConf
from src.utils.exceptions import NoLiveFullNodeException
from src.utils.timing import TimedTaskLimiter


def start_node_monitor(node_monitor: NodeMonitor, monitor_period: int,
                       logger: logging.Logger):
    # Start
    while True:
        # Read node data
        try:
            logger.debug('Reading %s.', node_monitor.node)
            node_monitor.monitor()
            logger.debug('Done reading %s.', node_monitor.node)
        except ReqConnectionError:
            node_monitor.node.set_as_down(node_monitor.channels, logger)
        except ReadTimeout:
            node_monitor.node.set_as_down(node_monitor.channels, logger)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            logger.error('Error when reading data from %s: %s. '
                         'Alerter will continue running normally.',
                         node_monitor.node, e)
        except Exception as e:
            logger.exception(e)
            raise e

        # Save all state
        node_monitor.save_state()
        node_monitor.node.save_state(logger)

        # Sleep
        logger.debug('Sleeping for %s seconds.', monitor_period)
        time.sleep(monitor_period)


def start_network_monitor(network_monitor: NetworkMonitor, monitor_period: int,
                          logger: logging.Logger):
    # Start
    while True:
        # Read network data
        try:
            logger.debug('Reading network data.')
            network_monitor.monitor()
            logger.debug('Done reading network data.')
        except NoLiveFullNodeException:
            network_monitor.channels.alert_major(
                CouldNotFindLiveFullNodeAlert(network_monitor.monitor_name))
        except (ReqConnectionError, ReadTimeout):
            network_monitor.last_full_node_used.set_as_down(
                network_monitor.channels, logger)
        except (IncompleteRead, ChunkedEncodingError, ProtocolError) as e:
            network_monitor.channels.alert_error(ErrorWhenReadingDataFromNode(
                network_monitor.last_full_node_used))
            logger.error('Error when reading data from %s: %s',
                         network_monitor.last_full_node_used, e)
        except Exception as e:
            logger.exception(e)
            raise e

        # Save all state
        network_monitor.save_state()

        # Sleep
        if not network_monitor.is_syncing():
            logger.debug('Sleeping for %s seconds.', monitor_period)
            time.sleep(monitor_period)


def start_github_monitor(github_monitor: GitHubMonitor, monitor_period: int,
                         logger: logging.Logger,
                         internal_config: InternalConfig = InternalConf):
    # Set up alert limiter
    github_error_alert_limiter = TimedTaskLimiter(
        internal_config.github_error_interval_seconds)

    # Start
    while True:
        # Read GitHub releases page
        try:
            logger.debug('Reading %s.', github_monitor.releases_page)
            github_monitor.monitor()
            logger.debug('Done reading %s.', github_monitor.releases_page)

            # Save all state
            github_monitor.save_state()

            # Reset alert limiter
            github_error_alert_limiter.reset()
        except (ReqConnectionError, ReadTimeout) as conn_err:
            if github_error_alert_limiter.can_do_task():
                github_monitor.channels.alert_error(
                    CannotAccessGitHubPageAlert(github_monitor.releases_page))
                github_error_alert_limiter.did_task()
            logger.error('Error occurred when accessing {}: {}.'
                         ''.format(github_monitor.releases_page, conn_err))
        except JSONDecodeError as json_error:
            logger.error(json_error)  # Ignore such errors
        except Exception as e:
            logger.exception(e)
            raise e

        # Sleep
        logger.debug('Sleeping for %s seconds.', monitor_period)
        time.sleep(monitor_period)
