import pytest
from unittest.mock import patch, MagicMock

from kryten.metrics.graphite import GraphiteMetricSender
from kryten.metrics.statsd import StatsDMetricSender
from kryten.metrics.prometheus import PrometheusMetricSender
from kryten.exceptions import ImpossibleRequestError


class TestGraphiteMetricSender:
    def test_init_calls_graphyte_init_with_correct_args(self):
        with patch("graphyte.init") as mock_init, patch("graphyte.send"):
            GraphiteMetricSender("graphite.example.com", prefix="myapp.data")
            mock_init.assert_called_once_with(
                host="graphite.example.com", prefix="myapp.data", interval=30
            )

    def test_send_metric_calls_graphyte_send(self):
        with patch("graphyte.init"), patch("graphyte.send") as mock_send:
            sender = GraphiteMetricSender("localhost")
            sender.send_metric("temperature", 21.5)
            mock_send.assert_called_once_with("temperature", 21.5)

    def test_send_metric_with_integer_value(self):
        with patch("graphyte.init"), patch("graphyte.send") as mock_send:
            sender = GraphiteMetricSender("localhost")
            sender.send_metric("count", 42)
            mock_send.assert_called_once_with("count", 42)


class TestStatsDMetricSender:
    def test_udp_mode_creates_stats_client(self):
        with patch("statsd.StatsClient") as mock_cls, patch("statsd.TCPStatsClient"):
            StatsDMetricSender("localhost", port=8125, udp=True)
            mock_cls.assert_called_once_with(
                host="localhost", port=8125, prefix="kryten.data"
            )

    def test_tcp_mode_creates_tcp_stats_client(self):
        with patch("statsd.TCPStatsClient") as mock_cls, patch("statsd.StatsClient"):
            StatsDMetricSender("localhost", port=8125, udp=False)
            mock_cls.assert_called_once_with(
                host="localhost", port=8125, prefix="kryten.data"
            )

    def test_send_metric_uses_gauge(self):
        with patch("statsd.StatsClient") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            sender = StatsDMetricSender("localhost")
            sender.send_metric("my_metric", 42.0)
            mock_client.gauge.assert_called_once_with("my_metric", 42.0)

    def test_send_metric_with_increment_uses_incr(self):
        with patch("statsd.StatsClient") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            sender = StatsDMetricSender("localhost")
            sender.send_metric("my_counter", 1, increment=True)
            mock_client.incr.assert_called_once_with("my_counter", 1)

    def test_send_metric_with_none_value_raises(self):
        with patch("statsd.StatsClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            sender = StatsDMetricSender("localhost")
            with pytest.raises(ImpossibleRequestError):
                sender.send_metric("my_metric", None)

    def test_default_prefix_is_used(self):
        with patch("statsd.StatsClient") as mock_cls:
            StatsDMetricSender("localhost")
            _, kwargs = mock_cls.call_args
            assert kwargs["prefix"] == "kryten.data"


class TestPrometheusMetricSender:
    def test_new_metric_creates_gauge_with_prefixed_name(self):
        with patch("prometheus_client.start_http_server"), \
             patch("prometheus_client.Gauge") as mock_gauge_cls:
            mock_gauge_cls.return_value = MagicMock()
            sender = PrometheusMetricSender("localhost")
            sender.send_metric("temperature", 21.5, tags={"room": "kitchen"},
                               metric_desc="Room temperature")
            call_args = mock_gauge_cls.call_args[0]
            assert call_args[0] == "kryten_temperature"
            assert call_args[1] == "Room temperature"

    def test_same_metric_name_reuses_existing_gauge(self):
        with patch("prometheus_client.start_http_server"), \
             patch("prometheus_client.Gauge") as mock_gauge_cls:
            mock_gauge_cls.return_value = MagicMock()
            sender = PrometheusMetricSender("localhost")
            sender.send_metric("temperature", 21.5, tags={"room": "kitchen"})
            sender.send_metric("temperature", 22.0, tags={"room": "kitchen"})
            assert mock_gauge_cls.call_count == 1

    def test_send_metric_calls_set_by_default(self):
        with patch("prometheus_client.start_http_server"), \
             patch("prometheus_client.Gauge") as mock_gauge_cls:
            mock_gauge = MagicMock()
            mock_gauge_cls.return_value = mock_gauge
            sender = PrometheusMetricSender("localhost")
            sender.send_metric("temperature", 21.5, tags={"room": "kitchen"})
            mock_gauge.labels.return_value.set.assert_called_once_with(21.5)

    def test_send_metric_with_increment_calls_inc(self):
        with patch("prometheus_client.start_http_server"), \
             patch("prometheus_client.Gauge") as mock_gauge_cls:
            mock_gauge = MagicMock()
            mock_gauge_cls.return_value = mock_gauge
            sender = PrometheusMetricSender("localhost")
            sender.send_metric("request_count", 1, increment=True, tags={"endpoint": "/api"})
            mock_gauge.labels.return_value.inc.assert_called_once_with(1)

    def test_metric_desc_defaults_to_prefixed_metric_name(self):
        with patch("prometheus_client.start_http_server"), \
             patch("prometheus_client.Gauge") as mock_gauge_cls:
            mock_gauge_cls.return_value = MagicMock()
            sender = PrometheusMetricSender("localhost")
            sender.send_metric("my_sensor", 1.0)
            call_args = mock_gauge_cls.call_args[0]
            assert call_args[1] == "kryten_my_sensor"

    def test_tags_are_passed_as_label_names(self):
        with patch("prometheus_client.start_http_server"), \
             patch("prometheus_client.Gauge") as mock_gauge_cls:
            mock_gauge = MagicMock()
            mock_gauge_cls.return_value = mock_gauge
            sender = PrometheusMetricSender("localhost")
            sender.send_metric("temp", 20.0, tags={"zone": "living_room", "home": "1"})
            label_names = list(mock_gauge_cls.call_args[0][2])
            assert "zone" in label_names
            assert "home" in label_names
