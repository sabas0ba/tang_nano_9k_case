ARG NIX_VERSION=2.35.1
ARG NIX_IMAGE_DIGEST=sha256:377d4887aca98f0dfa12971c1ea6d6a625a435d8b610d4c95a436843da6fbfd1
FROM nixos/nix:${NIX_VERSION}@${NIX_IMAGE_DIGEST}

RUN mkdir -p /etc/nix \
  && printf '%s\n' \
  'experimental-features = nix-command flakes' \
  'sandbox = false' \
  'filter-syscalls = false' \
  'max-jobs = auto' \
  'flake-registry = ' \
  >> /etc/nix/nix.conf

ENV CASE_PROFILE=/nix/var/nix/profiles/tang-nano-9k-case
WORKDIR /workspace

COPY flake.nix flake.lock ./
RUN nix develop --profile "$CASE_PROFILE" --command true \
  && nix flake archive --json > /dev/null \
  && nix registry add nixpkgs \
  "path:$(nix eval --raw --impure --expr '(builtins.getFlake "/workspace").inputs.nixpkgs.outPath')" \
  && rm -rf /root/.cache/nix

COPY . .
COPY scripts/container-entrypoint.sh /usr/local/bin/case-entrypoint.sh
RUN chmod +x /usr/local/bin/case-entrypoint.sh

ENTRYPOINT ["/bin/sh", "/usr/local/bin/case-entrypoint.sh"]
CMD []
