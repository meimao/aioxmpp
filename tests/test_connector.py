########################################################################
# File name: test_connector.py
# This file is part of: aioxmpp
#
# LICENSE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
########################################################################
import asyncio
import contextlib
import logging
import unittest
import unittest.mock

import aioxmpp.connector as connector
import aioxmpp.errors as errors
import aioxmpp.nonza as nonza

from aioxmpp.utils import namespaces

from aioxmpp.testutils import (
    run_coroutine,
    CoroutineMock,
)


class TestSTARTTLSConnector(unittest.TestCase):
    def setUp(self):
        self.c = connector.STARTTLSConnector()

    def tearDown(self):
        del self.c

    def test_tls_supported(self):
        self.assertTrue(
            self.c.tls_supported
        )

    def test_connect_successful(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()
        features[...] = nonza.StartTLSFeature()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base_logger = unittest.mock.Mock(spec=logging.Logger)

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.send_and_wait_for = CoroutineMock()
        base.send_and_wait_for.return_value = unittest.mock.Mock(
            spec=nonza.StartTLSProceed,
        )
        base.certificate_verifier.pre_handshake = CoroutineMock()
        base.metadata.certificate_verifier_factory.return_value = \
            base.certificate_verifier
        base.metadata.ssl_context_factory.return_value = \
            unittest.mock.sentinel.ssl_context
        base.reset_stream_and_get_features = CoroutineMock()
        base.reset_stream_and_get_features.return_value = \
            unittest.mock.sentinel.reset
        base.async_.return_value = unittest.mock.sentinel.features_future

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            StartTLS_nonza = stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.nonza.StartTLS",
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.reset_stream_and_get_features",
                    new=base.reset_stream_and_get_features,
                )
            )

            result = run_coroutine(self.c.connect(
                unittest.mock.sentinel.loop,
                base.metadata,
                unittest.mock.sentinel.domain,
                unittest.mock.sentinel.host,
                unittest.mock.sentinel.port,
                unittest.mock.sentinel.timeout,
                base_logger=base_logger,
            ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=base_logger,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.send_and_wait_for(
                    base.protocol,
                    [
                        StartTLS_nonza(),
                    ],
                    [
                        nonza.StartTLSFailure,
                        nonza.StartTLSProceed,
                    ]
                ),
                unittest.mock.call.metadata.certificate_verifier_factory(),
                unittest.mock.call.certificate_verifier.pre_handshake(
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    base.metadata,
                ),
                unittest.mock.call.metadata.ssl_context_factory(),
                unittest.mock.call.certificate_verifier.setup_context(
                    unittest.mock.sentinel.ssl_context,
                    unittest.mock.sentinel.transport,
                ),
                unittest.mock.call.protocol.starttls(
                    ssl_context=unittest.mock.sentinel.ssl_context,
                    post_handshake_callback=
                        base.certificate_verifier.post_handshake,
                ),
                unittest.mock.call.reset_stream_and_get_features(
                    base.protocol,
                    timeout=unittest.mock.sentinel.timeout,
                ),
            ]
        )

        self.assertEqual(
            result,
            (
                unittest.mock.sentinel.transport,
                base.protocol,
                unittest.mock.sentinel.reset,
            )
        )

    def test_abort_xmlstream_if_connect_fails(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()
        features[...] = nonza.StartTLSFeature()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.side_effect = Exception()
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.reset_stream_and_get_features",
                    new=base.reset_stream_and_get_features,
                )
            )

            with self.assertRaises(Exception):
                run_coroutine(self.c.connect(
                    unittest.mock.sentinel.loop,
                    base.metadata,
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    unittest.mock.sentinel.timeout,
                ))

        self.maxDiff = None

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.protocol.abort(),
            ]
        )

    def test_connect_without_starttls_support_and_with_required_success(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.send_and_wait_for = CoroutineMock()
        base.send_and_wait_for.return_value = unittest.mock.Mock(
            spec=nonza.StartTLSProceed,
        )
        base.certificate_verifier.pre_handshake = CoroutineMock()
        base.metadata.certificate_verifier_factory.return_value = \
            base.certificate_verifier
        base.metadata.ssl_context_factory.return_value = \
            unittest.mock.sentinel.ssl_context
        base.reset_stream_and_get_features = CoroutineMock()
        base.reset_stream_and_get_features.return_value = \
            unittest.mock.sentinel.reset
        base.async_.return_value = unittest.mock.sentinel.features_future

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            StartTLS_nonza = stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.nonza.StartTLS",
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.reset_stream_and_get_features",
                    new=base.reset_stream_and_get_features,
                )
            )

            result = run_coroutine(self.c.connect(
                unittest.mock.sentinel.loop,
                base.metadata,
                unittest.mock.sentinel.domain,
                unittest.mock.sentinel.host,
                unittest.mock.sentinel.port,
                unittest.mock.sentinel.timeout,
            ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.send_and_wait_for(
                    base.protocol,
                    [
                        StartTLS_nonza(),
                    ],
                    [
                        nonza.StartTLSFailure,
                        nonza.StartTLSProceed,
                    ]
                ),
                unittest.mock.call.metadata.certificate_verifier_factory(),
                unittest.mock.call.certificate_verifier.pre_handshake(
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    base.metadata,
                ),
                unittest.mock.call.metadata.ssl_context_factory(),
                unittest.mock.call.certificate_verifier.setup_context(
                    unittest.mock.sentinel.ssl_context,
                    unittest.mock.sentinel.transport,
                ),
                unittest.mock.call.protocol.starttls(
                    ssl_context=unittest.mock.sentinel.ssl_context,
                    post_handshake_callback=
                        base.certificate_verifier.post_handshake,
                ),
                unittest.mock.call.reset_stream_and_get_features(
                    base.protocol,
                    timeout=unittest.mock.sentinel.timeout,
                ),
            ]
        )

        self.assertEqual(
            result,
            (
                unittest.mock.sentinel.transport,
                base.protocol,
                unittest.mock.sentinel.reset,
            )
        )

    def test_connect_without_starttls_support_and_with_required_failure(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.send_and_wait_for = CoroutineMock()
        base.send_and_wait_for.return_value = unittest.mock.Mock(
            spec=nonza.StartTLSFailure,
        )

        error_message = (
            "server failed to STARTTLS"
        )

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            StartTLS_nonza = stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.nonza.StartTLS",
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_stream_error_and_close",
                    new=base.send_stream_error_and_close
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.async",
                    new=base.async_,
                )
            )

            with self.assertRaisesRegex(errors.TLSUnavailable, error_message):
                run_coroutine(self.c.connect(
                    unittest.mock.sentinel.loop,
                    base.metadata,
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    unittest.mock.sentinel.timeout,
                ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.send_and_wait_for(
                    base.protocol,
                    [
                        StartTLS_nonza(),
                    ],
                    [
                        nonza.StartTLSFailure,
                        nonza.StartTLSProceed,
                    ]
                ),
                unittest.mock.call.send_stream_error_and_close(
                    base.protocol,
                    condition=(namespaces.streams, "policy-violation"),
                    text=error_message,
                )
            ]
        )

    def test_connect_without_starttls_support_and_with_required_error(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.send_and_wait_for = CoroutineMock()
        base.send_and_wait_for.side_effect = errors.StreamError(
            condition=(namespaces.streams, "unsupported-stanza-type"),
        )

        error_message = (
            "STARTTLS not supported by server, but required by client"
        )

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            StartTLS_nonza = stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.nonza.StartTLS",
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_stream_error_and_close",
                    new=base.send_stream_error_and_close
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.async",
                    new=base.async_,
                )
            )

            with self.assertRaisesRegex(errors.TLSUnavailable, error_message):
                run_coroutine(self.c.connect(
                    unittest.mock.sentinel.loop,
                    base.metadata,
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    unittest.mock.sentinel.timeout,
                ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.send_and_wait_for(
                    base.protocol,
                    [
                        StartTLS_nonza(),
                    ],
                    [
                        nonza.StartTLSFailure,
                        nonza.StartTLSProceed,
                    ]
                )
            ]
        )

    def test_connect_without_starttls_support_and_without_required(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = False
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_stream_error_and_close",
                    new=base.send_stream_error_and_close,
                )
            )

            result = run_coroutine(self.c.connect(
                unittest.mock.sentinel.loop,
                base.metadata,
                unittest.mock.sentinel.domain,
                unittest.mock.sentinel.host,
                unittest.mock.sentinel.port,
                unittest.mock.sentinel.timeout,
            ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
            ]
        )

        self.assertEqual(
            result,
            (
                unittest.mock.sentinel.transport,
                base.protocol,
                features,
            )
        )

    def test_connect_with_failed_starttls_and_with_required(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()
        features[...] = nonza.StartTLSFeature()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.send_and_wait_for = CoroutineMock()
        base.send_and_wait_for.return_value = unittest.mock.Mock(
            spec=nonza.StartTLSFailure,
        )

        error_message = (
            "server failed to STARTTLS"
        )

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            StartTLS_nonza = stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.nonza.StartTLS",
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_stream_error_and_close",
                    new=base.send_stream_error_and_close
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.async",
                    new=base.async_,
                )
            )

            with self.assertRaisesRegex(errors.TLSUnavailable, error_message):
                run_coroutine(self.c.connect(
                    unittest.mock.sentinel.loop,
                    base.metadata,
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    unittest.mock.sentinel.timeout,
                ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.send_and_wait_for(
                    base.protocol,
                    [
                        StartTLS_nonza(),
                    ],
                    [
                        nonza.StartTLSFailure,
                        nonza.StartTLSProceed,
                    ]
                ),
                unittest.mock.call.send_stream_error_and_close(
                    base.protocol,
                    condition=(namespaces.streams, "policy-violation"),
                    text=error_message,
                )
            ]
        )

    def test_connect_with_failed_starttls_and_without_required(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features = nonza.StreamFeatures()
        features[...] = nonza.StartTLSFeature()

        features_future = asyncio.Future()
        features_future.set_result(
            features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = False
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.send_and_wait_for = CoroutineMock()
        base.send_and_wait_for.return_value = unittest.mock.Mock(
            spec=nonza.StartTLSFailure,
        )

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            StartTLS_nonza = stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.nonza.StartTLS",
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_and_wait_for",
                    new=base.send_and_wait_for,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.send_stream_error_and_close",
                    new=base.send_stream_error_and_close
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.async",
                    new=base.async_,
                )
            )

            result = run_coroutine(self.c.connect(
                unittest.mock.sentinel.loop,
                base.metadata,
                unittest.mock.sentinel.domain,
                unittest.mock.sentinel.host,
                unittest.mock.sentinel.port,
                unittest.mock.sentinel.timeout,
            ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    use_starttls=True,
                ),
                unittest.mock.call.send_and_wait_for(
                    base.protocol,
                    [
                        StartTLS_nonza(),
                    ],
                    [
                        nonza.StartTLSFailure,
                        nonza.StartTLSProceed,
                    ]
                )
            ]
        )

        self.assertEqual(
            result,
            (
                unittest.mock.sentinel.transport,
                base.protocol,
                features,
            )
        )


class TestXMPPOverTLSConnector(unittest.TestCase):
    def setUp(self):
        self.c = connector.XMPPOverTLSConnector()

    def tearDown(self):
        del self.c

    def test_tls_supported(self):
        self.assertTrue(
            self.c.tls_supported
        )

    def test_connect_with_tls(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features_future = asyncio.Future()
        features_future.set_result(
            unittest.mock.sentinel.features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.return_value = (
            unittest.mock.sentinel.transport,
            base.protocol,
        )
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.certificate_verifier.pre_handshake = CoroutineMock()
        base.metadata.certificate_verifier_factory.return_value = \
            base.certificate_verifier
        # base.metadata.ssl_context_factory.return_value = \
        #     unittest.mock.sentinel.ssl_context

        base_logger = unittest.mock.Mock(spec=logging.Logger)

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            result = run_coroutine(self.c.connect(
                unittest.mock.sentinel.loop,
                base.metadata,
                unittest.mock.sentinel.domain,
                unittest.mock.sentinel.host,
                unittest.mock.sentinel.port,
                unittest.mock.sentinel.timeout,
                base_logger=base_logger,
            ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=base_logger,
                ),
                unittest.mock.call.metadata.certificate_verifier_factory(),
                unittest.mock.call.certificate_verifier.pre_handshake(
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    base.metadata,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    post_handshake_callback=
                        base.certificate_verifier.post_handshake,
                    ssl_context_factory=unittest.mock.ANY,
                    use_starttls=False,
                ),
            ]
        )

        _, _, kwargs = base.mock_calls[-1]
        factory = kwargs.pop("ssl_context_factory")

        base.mock_calls.clear()

        ssl_context = factory(unittest.mock.sentinel.passed_transport)

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.metadata.ssl_context_factory(),
                unittest.mock.call.metadata.
                    ssl_context_factory().set_alpn_protos([b"xmpp-client"]),
                unittest.mock.call.certificate_verifier.setup_context(
                    ssl_context,
                    unittest.mock.sentinel.passed_transport,
                ),
            ]
        )

        self.assertEqual(
            ssl_context,
            base.metadata.ssl_context_factory()
        )

        self.assertEqual(
            result,
            (
                unittest.mock.sentinel.transport,
                base.protocol,
                unittest.mock.sentinel.features,
            )
        )

        # test for correct generation of warnings if set_alpn_proto is
        # not available
        base.mock_calls.clear()
        base_logger.mock_calls.clear()

        ssl_context = base.metadata.ssl_context_factory.return_value = \
            unittest.mock.Mock()
        del ssl_context.set_alpn_protos
        ssl_context = factory(unittest.mock.sentinel.passed_transport)

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.metadata.ssl_context_factory(),
                unittest.mock.call.certificate_verifier.setup_context(
                    ssl_context,
                    unittest.mock.sentinel.passed_transport,
                ),
            ]
        )

        self.assertSequenceEqual(
            base_logger.mock_calls,
            [
                unittest.mock.call.getChild().warning(
                    "OpenSSL.SSL.Context lacks set_alpn_protos - "
                    "please update pyOpenSSL to a recent version"
                ),
            ]
        )

        base.mock_calls.clear()
        base_logger.mock_calls.clear()

        ssl_context = base.metadata.ssl_context_factory.return_value = \
            unittest.mock.Mock()
        ssl_context.set_alpn_protos.side_effect = NotImplementedError
        ssl_context = factory(unittest.mock.sentinel.passed_transport)

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.metadata.ssl_context_factory(),
                unittest.mock.call.metadata.
                    ssl_context_factory().set_alpn_protos([b"xmpp-client"]),
                unittest.mock.call.certificate_verifier.setup_context(
                    ssl_context,
                    unittest.mock.sentinel.passed_transport,
                ),
            ]
        )

        self.assertSequenceEqual(
            base_logger.mock_calls,
            [
                unittest.mock.call.getChild().warning(
                    "the underlying OpenSSL library does not support ALPN"
                ),
            ]
        )

    def test_abort_XMLStream_whin_connect_raises(self):
        captured_features_future = None

        def capture_future(*args, features_future=None, **kwargs):
            nonlocal captured_features_future
            captured_features_future = features_future
            return base.protocol

        features_future = asyncio.Future()
        features_future.set_result(
            unittest.mock.sentinel.features
        )

        base = unittest.mock.Mock()
        base.protocol.starttls = CoroutineMock()
        base.create_starttls_connection = CoroutineMock()
        base.create_starttls_connection.side_effect = Exception()
        base.metadata.tls_required = True
        base.XMLStream.return_value = base.protocol
        base.XMLStream.side_effect = capture_future
        base.Future.return_value = features_future
        base.certificate_verifier.pre_handshake = CoroutineMock()
        base.metadata.certificate_verifier_factory.return_value = \
            base.certificate_verifier
        base.metadata.ssl_context_factory.return_value = \
            unittest.mock.sentinel.ssl_context

        with contextlib.ExitStack() as stack:
            stack.enter_context(
                unittest.mock.patch(
                    "asyncio.Future",
                    new=base.Future,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.ssl_transport.create_starttls_connection",
                    new=base.create_starttls_connection,
                )
            )

            stack.enter_context(
                unittest.mock.patch(
                    "aioxmpp.protocol.XMLStream",
                    new=base.XMLStream,
                )
            )

            with self.assertRaises(Exception):
                run_coroutine(self.c.connect(
                    unittest.mock.sentinel.loop,
                    base.metadata,
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    unittest.mock.sentinel.timeout,
                ))

        self.assertSequenceEqual(
            base.mock_calls,
            [
                unittest.mock.call.Future(
                    loop=unittest.mock.sentinel.loop,
                ),
                unittest.mock.call.XMLStream(
                    to=unittest.mock.sentinel.domain,
                    features_future=features_future,
                    base_logger=None,
                ),
                unittest.mock.call.metadata.certificate_verifier_factory(),
                unittest.mock.call.certificate_verifier.pre_handshake(
                    unittest.mock.sentinel.domain,
                    unittest.mock.sentinel.host,
                    unittest.mock.sentinel.port,
                    base.metadata,
                ),
                unittest.mock.call.create_starttls_connection(
                    unittest.mock.sentinel.loop,
                    unittest.mock.ANY,
                    host=unittest.mock.sentinel.host,
                    port=unittest.mock.sentinel.port,
                    peer_hostname=unittest.mock.sentinel.host,
                    server_hostname=unittest.mock.sentinel.domain,
                    post_handshake_callback=
                        base.certificate_verifier.post_handshake,
                    ssl_context_factory=unittest.mock.ANY,
                    use_starttls=False,
                ),
                unittest.mock.call.protocol.abort()
            ]
        )
