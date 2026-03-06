FROM lscr.io/linuxserver/code-server:latest

# Install dependencies for curl
RUN apt-get update && \
    apt-get install -y xz-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create directory for nix
RUN mkdir /nix
RUN curl -L https://nixos.org/nix/install | sh -s -- --daemon
# Run nix-daemon
CMD ["/nix/var/nix/profiles/default/bin/nix-daemon", "--daemon"]

RUN printf '%s\n' \
  'extra-experimental-features = nix-command flakes' \
  'sandbox = false' \
  'trusted-users = root abc' \
  > /etc/nix/nix.conf

# Set the environment variable to use nix
ENV NIX_PROFILES="/nix/var/nix/profiles/default /root/.nix-profile"
ENV NIX_PATH="nixpkgs=/nix/var/nix/profiles/per-user/root/channels/nixpkgs"

ENTRYPOINT ["/init"]
