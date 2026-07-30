"""Infrastructure layer — mọi thứ liên quan đến I/O, hệ thống, network.

Nguyên tắc:
  - Chỉ chứa wrappers, không chứa business logic.
  - Dễ mock để test (inject fake).
  - Tương lai sẽ có async wrappers bên cạnh sync wrappers (Phase C).
"""