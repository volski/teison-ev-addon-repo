import * as forge from 'node-forge';

const publicKeyPem = `-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDKzH8tu+lGYMkT61r7FCdBZ/ez
lLg22grOvvuQ76NtwGPeAUklREWJqArQgd4U6RCx0vVCT6gtBOtXUK2NkSJvKjUW
BhRp6in5VJikMp1+KxyO2vgjIrKMDWzucuoeozBQ89LhhyoB2Sp3jpxKpb83/Pqu
p0gQXJmL39hJ3O+HlwIDAQAB
-----END PUBLIC KEY-----`;

export function encrypt(message: string): string {
  const publicKey = forge.pki.publicKeyFromPem(publicKeyPem);
  const encrypted = publicKey.encrypt(message, 'RSAES-PKCS1-V1_5');
  const b64 = forge.util.encode64(encrypted);
  return toUrlSafeBase64(b64);
}
function toUrlSafeBase64(input: string): string {
    return input.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}