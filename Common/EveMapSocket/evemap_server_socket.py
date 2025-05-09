from typing import Final

from evemap_base_socket import EveMapBaseSocket
from evemap_conn_socket import EveMapConnSocket

PORT: Final[int] = 6000


class EveMapServerSocket(EveMapBaseSocket):
    def accept(self) -> tuple[EveMapConnSocket, tuple[str, int]]:
        conn, address = self.tcp_socket.accept()
        return EveMapConnSocket(conn), address

    def bind_and_listen(self, host: str) -> None:
        self.tcp_socket.bind((host, PORT))
        self.tcp_socket.listen(5)
